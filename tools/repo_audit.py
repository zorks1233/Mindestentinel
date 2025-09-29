#!/usr/bin/env python3
"""
repo_audit.py

Ein lokales Audit-Tool für dein Projekt (keine Änderungen an Dateien).
Es sucht nach Syntax-Fehlern, unsicheren Patterns, circular imports,
Problemen in Batch/Shell Startskripten, fehlendem pinning und Modell-Ordner-Checks.

Usage:
  python3 tools/repo_audit.py
Salida: stdout Report (auch in audit_output.txt speichern empfohlen).
"""
import os
import sys
import ast
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set

ROOT = Path(".").resolve()

# heuristics
MODEL_FILES = ["config.json", "pytorch_model.bin", "model.safetensors", "tf_model.h5"]
PY_EXTS = [".py"]
SHELL_EXTS = [".sh", ".bash"]
BATCH_EXTS = [".bat", ".cmd"]
UNSAFE_PATTERNS = [
    r"\bexec\(", r"\beval\(", r"os\.system\(", r"subprocess\.", r"pickle\.loads\(",
    r"yaml\.load\(", r"open\([^,]+['\"]w", # naive write detection
]
SECRET_PATTERNS = [r"API[_-]?KEY", r"SECRET", r"PASSWORD", r"TOKEN", r"MIND_"]
TODO_PATTERNS = [r"\bTODO\b", r"\bFIXME\b", r"\bXXX\b", r"\bHACK\b"]
INFINITE_LOOP_PATTERN = r"while\s+True\b"

report = {"syntax_errors": [], "unsafe": [], "secrets": [], "todos": [], "infinite_loops": [], "circular_imports": [], "bad_future": [], "batch_issues": [], "model_warnings": [], "requirements": []}

def list_files() -> List[Path]:
    exts = PY_EXTS + SHELL_EXTS + BATCH_EXTS + [".yaml", ".yml", ".json"]
    result = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            result.append(p)
    return sorted(result)

def check_syntax(py_path: Path):
    try:
        src = py_path.read_text(encoding="utf-8", errors="replace")
        compile(src, str(py_path), "exec")
    except SyntaxError as e:
        report["syntax_errors"].append((str(py_path), e.lineno, str(e)))
    except Exception as e:
        report["syntax_errors"].append((str(py_path), None, f"parse error: {e}"))

def check_future_top(py_path: Path):
    txt = py_path.read_text(encoding="utf-8", errors="replace")
    # find first non-empty, non-shebang, non-comment line index
    lines = txt.splitlines()
    first_code_line = None
    for i, L in enumerate(lines):
        s = L.strip()
        if s == "" or s.startswith("#") or s.startswith("'''") or s.startswith('"""'):
            continue
        first_code_line = (i+1, s)
        break
    if first_code_line and "from __future__ import" in txt:
        # ensure from __future__ occurs before other code (except shebang/comments)
        idx = next((i for i,L in enumerate(lines) if "from __future__ import" in L), None)
        if idx is not None and idx+1 != first_code_line[0]:
            report["bad_future"].append((str(py_path), idx+1, "from __future__ should be at file top (after shebang/comments)"))

def scan_unsafe(py_path: Path):
    txt = py_path.read_text(encoding="utf-8", errors="replace")
    for pat in UNSAFE_PATTERNS:
        for m in re.finditer(pat, txt):
            report["unsafe"].append((str(py_path), py_path.read_text().count("\n", 0, m.start())+1 if m else None, pat))

def scan_secrets(p: Path):
    txt = p.read_text(encoding="utf-8", errors="replace")
    for pat in SECRET_PATTERNS:
        for m in re.finditer(pat, txt, flags=re.IGNORECASE):
            report["secrets"].append((str(p), p.read_text().count("\n", 0, m.start())+1 if m else None, m.group(0)))

def scan_todos(p: Path):
    txt = p.read_text(encoding="utf-8", errors="replace")
    for pat in TODO_PATTERNS:
        for m in re.finditer(pat, txt):
            report["todos"].append((str(p), p.read_text().count("\n", 0, m.start())+1, m.group(0)))

def scan_loops(p: Path):
    txt = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(INFINITE_LOOP_PATTERN, txt):
        ln = txt.count("\n", 0, m.start())+1
        # naive: check if there is time.sleep within next ~20 lines
        following = "\n".join(txt.splitlines()[ln-1:ln+20])
        if "time.sleep" not in following:
            report["infinite_loops"].append((str(p), ln, "while True without nearby sleep"))

def build_import_graph(py_files: List[Path]) -> Dict[str, Set[str]]:
    graph = {}
    for p in py_files:
        key = str(p.relative_to(ROOT))
        graph.setdefault(key, set())
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        graph[key].add(n.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        graph[key].add(node.module.split(".")[0])
        except Exception:
            pass
    return graph

def detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    # simple cycle detection on filename->module names: best-effort mapping
    # Build mapping module_name -> file(s)
    module_to_files = {}
    for f in graph:
        mod = Path(f).stem
        module_to_files.setdefault(mod, []).append(f)
    # convert graph to file->file edges where module maps to file(s)
    file_graph = {f: set() for f in graph}
    for f, imports in graph.items():
        for im in imports:
            if im in module_to_files:
                for target in module_to_files[im]:
                    file_graph[f].add(target)
    # detect simple cycles via DFS
    cycles = []
    visited = set()
    stack = []
    def dfs(u, path):
        visited.add(u)
        path.append(u)
        for v in file_graph.get(u, []):
            if v in path:
                cycles.append(path[path.index(v):] + [v])
            elif v not in visited:
                dfs(v, path.copy())
    for node in file_graph:
        if node not in visited:
            dfs(node, [])
    return cycles

def check_batch_scripts():
    # find .bat/.sh that start python and whether they forward args correctly
    for p in ROOT.rglob("*"):
        if p.suffix.lower() in BATCH_EXTS + SHELL_EXTS:
            txt = p.read_text(encoding="utf-8", errors="replace")
            if "python" in txt.lower():
                if p.suffix.lower() in BATCH_EXTS:
                    if "%*" not in txt and "%1" not in txt:
                        report["batch_issues"].append((str(p), "batch script seems not forwarding args to python (missing %*)"))
                else:
                    if "$@" not in txt and "$*" not in txt:
                        report["batch_issues"].append((str(p), "shell script seems not forwarding args to python (missing \"$@\" or $*)"))

def check_model_dirs():
    # look for folders named models, model, data/models
    candidate_dirs = []
    for p in ["models", "data/models", "data/model", "model"]:
        candidate = ROOT.joinpath(p)
        if candidate.exists() and candidate.is_dir():
            candidate_dirs.append(candidate)
    for d in candidate_dirs:
        for child in d.iterdir():
            if child.is_dir():
                has = False
                for mf in MODEL_FILES:
                    if (child / mf).exists():
                        has = True
                if not has:
                    report["model_warnings"].append((str(child), "no recognized model files found (config.json/pytorch_model.bin/*.safetensors)"))

def check_requirements():
    if not (ROOT / "requirements-pinned.txt").exists() and (ROOT / "requirements.txt").exists():
        report["requirements"].append(("requirements.txt", "no pinned requirements-pinned.txt found; pinning recommended"))

def main():
    print("Repo Audit starting at:", ROOT)
    files = list_files()
    py_files = [f for f in files if f.suffix.lower() == ".py"]
    for p in py_files:
        check_syntax(p)
        check_future_top(p)
        scan_unsafe(p)
        scan_secrets(p)
        scan_todos(p)
        scan_loops(p)
    graph = build_import_graph(py_files)
    cycles = detect_cycles(graph)
    if cycles:
        for c in cycles:
            report["circular_imports"].append(c)
    check_batch_scripts()
    check_model_dirs()
    check_requirements()

    # Pretty print report
    def print_section(key, items, title, limit=200):
        print("\n" + "="*80)
        print(f"{title} ({len(items)})")
        print("-"*80)
        for i, it in enumerate(items[:limit]):
            print(i+1, ":", it)
    print_section("syntax_errors", report["syntax_errors"], "Syntax Errors")
    print_section("bad_future", report["bad_future"], "Misplaced __future__ imports")
    print_section("circular_imports", report["circular_imports"], "Circular Import Candidates")
    print_section("unsafe", report["unsafe"], "Unsafe Patterns (exec/eval/subprocess/yaml.load/... )")
    print_section("secrets", report["secrets"], "Hardcoded Secret-like Tokens")
    print_section("todos", report["todos"], "TODO/FIXME/XXX/HACK markings")
    print_section("infinite_loops", report["infinite_loops"], "Suspected Infinite Loops without sleep")
    print_section("batch_issues", report["batch_issues"], "Batch/Shell Script Issues (arg forwarding)")
    print_section("model_warnings", report["model_warnings"], "Model Directory Warnings")
    print_section("requirements", report["requirements"], "Requirements / Pinning Warnings")
    print("\n\nSummary & Quick Actions:")
    print("- Fix Syntax Errors first (they block startup).")
    print("- Move 'from __future__ import ...' to top if reported.")
    print("- Resolve circular imports by making imports local or using TYPE_CHECKING.")
    print("- Remove or whitelist subprocess/exec usages; replace yaml.load with yaml.safe_load.")
    print("- Remove hardcoded secrets and use env vars + .env or system secret manager.")
    print("- Ensure start scripts forward args to python (use %* or \"$@\").")
    print("- If large simulations: ensure SimulationManager, checkpointing and kill-switch exist.")
    print("\nEnd of report.")

if __name__ == "__main__":
    main()
