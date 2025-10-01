#!/usr/bin/env python3
"""
repo_audit_extended.py

Erweitertes Audit-Tool für build0015.4A (Windows safe).
Checks:
 - Syntax errors
 - misplaced from __future__
 - unsafe patterns (eval/exec/pickle/yaml.load/subprocess)
 - secrets / hardcoded tokens / DB URLs with password
 - password hashing usage (bcrypt/argon2 vs hashlib)
 - JWT/token heuristics (jwt.encode/decode, exp claim)
 - SQL execute patterns that look vulnerable to injection (f-strings, + concat, %)
 - shell/batch arg forwarding
 - simulation / checkpoint hints (simulate/SimulationManager)
 - model directory sanity
Output: human-readable report to stdout (redirect to file).
Usage (Windows):
  python tools\repo_audit_extended.py > audit_output.txt 2>&1
"""
import os, sys, re, ast, json
from pathlib import Path
from typing import List, Dict, Set

ROOT = Path(".").resolve()

PY_EXTS = [".py"]
SHELL_EXTS = [".sh", ".bash"]
BATCH_EXTS = [".bat", ".cmd"]
CONF_EXTS = [".yml", ".yaml", ".json"]

UNSAFE_PATTERNS = [
    r"\beval\(", r"\bexec\(", r"pickle\.loads\(", r"yaml\.load\(", r"os\.system\(", r"subprocess\.Popen\(", r"subprocess\.run\(",
]
SECRET_PATTERNS = [r"API[_-]?KEY", r"SECRET", r"PASSWORD", r"TOKEN", r"PRIVATE[_-]?KEY", r"MIND_"]
DB_URL_PATTERNS = [r"(postgresql?:\/\/[^'\"]+:[^'\"]+@)", r"(mysql:\/\/[^'\"]+:[^'\"]+@)", r"(mongodb:\/\/[^'\"]+:[^'\"]+@)", r"sqlite:\/\/\/?[^'\"]+"]
JWT_PATTERNS = [r"\bjwt\.encode\b", r"\bjwt\.decode\b", r"\bPyJWT\b", r"\bjwt\b"]
PASSWORD_HASH_LIBS = [r"\bbcrypt\b", r"\bargon2\b", r"\bpasslib\b"]
WEAK_HASH_PATTERNS = [r"hashlib\.sha1", r"hashlib\.sha224", r"hashlib\.md5", r"\bsha1\(", r"\bmd5\("]

SQL_EXEC_PATTERNS = [r"\.execute\(", r"\.executemany\("]
FSTRING_PATTERN = r"(f['\"])"
FORMAT_PATTERN = r"\.format\("
PERCENT_PATTERN = r"%\s*\("

INFINITE_LOOP_PATTERN = r"while\s+True\b"

MODEL_FILE_CANDIDATES = ["config.json", "pytorch_model.bin", "model.safetensors", "tf_model.h5"]

report = {
    "syntax_errors": [],
    "bad_future": [],
    "unsafe": [],
    "secrets": [],
    "db_urls": [],
    "jwt": [],
    "hashing": [],
    "sql_risk": [],
    "infinite_loops": [],
    "batch_issues": [],
    "simulation_hints": [],
    "model_warnings": [],
    "todos": []
}

def read_text_robust(path: Path) -> str:
    try:
        b = path.read_bytes()
    except Exception:
        return ""
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("utf-8", errors="replace")

def list_targets() -> List[Path]:
    exts = PY_EXTS + SHELL_EXTS + BATCH_EXTS + CONF_EXTS
    result = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            result.append(p)
    return sorted(result)

def check_syntax(p: Path):
    if p.suffix.lower() != ".py":
        return
    txt = read_text_robust(p)
    if not txt:
        return
    try:
        compile(txt, str(p), "exec")
    except SyntaxError as e:
        report["syntax_errors"].append((str(p), e.lineno, str(e)))
    except Exception as e:
        report["syntax_errors"].append((str(p), None, f"parse error: {e}"))

def check_future(p: Path):
    if p.suffix.lower() != ".py":
        return
    txt = read_text_robust(p)
    if "from __future__ import" in txt:
        # first non-comment line must be future import
        lines = txt.splitlines()
        first_code_idx = None
        for i,L in enumerate(lines):
            s = L.strip()
            if s == "" or s.startswith("#") or s.startswith("'''") or s.startswith('"""'):
                continue
            first_code_idx = i+1
            break
        idx = next((i+1 for i,L in enumerate(lines) if "from __future__ import" in L), None)
        if idx and first_code_idx and idx != first_code_idx:
            report["bad_future"].append((str(p), idx, "from __future__ must be top of file"))

def pattern_search(p: Path, patterns: List[str], key: str):
    txt = read_text_robust(p)
    if not txt:
        return
    for pat in patterns:
        for m in re.finditer(pat, txt, flags=re.IGNORECASE):
            ln = txt.count("\n", 0, m.start()) + 1
            report[key].append((str(p), ln, pat.strip()))

def sql_risk_scan(p: Path):
    if p.suffix.lower() != ".py":
        return
    txt = read_text_robust(p)
    if not txt:
        return
    # naive detection: .execute( with f" or .format or % formatting or + concatenation near execute
    for m in re.finditer(r"\.execute\((.*?)\)", txt, flags=re.DOTALL):
        snippet = m.group(1)[:200]
        ln = txt.count("\n", 0, m.start()) + 1
        risky = False
        if re.search(FSTRING_PATTERN, snippet):
            risky = True
            reason = "f-string inside execute"
        elif re.search(FORMAT_PATTERN, snippet):
            risky = True
            reason = ".format() used inside execute"
        elif re.search(PERCENT_PATTERN, snippet):
            risky = True
            reason = "% formatting inside execute"
        elif "+" in snippet:
            # plus could be concat — warn heuristically
            reason = "possible string concatenation inside execute"
            risky = True
        else:
            reason = "execute() usage"
        if risky:
            report["sql_risk"].append((str(p), ln, reason, snippet.replace("\n","\\n")))
    # also look for cursor.execute SQL built via f-string earlier
    for m in re.finditer(r"f['\"].*{.*}.*['\"]", txt, flags=re.DOTALL):
        ln = txt.count("\n", 0, m.start()) + 1
        report["sql_risk"].append((str(p), ln, "f-string detected (possible unsanitized interpolation)", m.group(0)[:200].replace("\n","\\n")))

def jwt_and_token_checks(p: Path):
    txt = read_text_robust(p)
    if not txt:
        return
    for m in re.finditer(r"\bjwt\.encode\b|\bjwt\.decode\b", txt):
        ln = txt.count("\n", 0, m.start()) + 1
        # Try to detect 'exp' claim usage heuristically
        # If 'exp' not in nearby lines -> warn
        nearby = "\n".join(txt.splitlines()[max(0,ln-3):ln+5])
        if "exp" not in nearby and "expiration" not in nearby and "exp=" not in nearby:
            report["jwt"].append((str(p), ln, "jwt usage found; no 'exp' claim detected nearby (heuristic)"))
        else:
            report["jwt"].append((str(p), ln, "jwt usage; exp detected (ok-ish)"))
    # detect PyJWT none-alg usage
    if re.search(r"alg\s*=\s*['\"]?none['\"]?", txt, flags=re.IGNORECASE):
        report["jwt"].append((str(p), None, "usage of alg='none' detected (CRITICAL)"))

def hashing_checks(p: Path):
    txt = read_text_robust(p)
    if not txt:
        return
    # Good libs
    if re.search(r"\b(bcrypt|argon2|passlib)\b", txt, flags=re.IGNORECASE):
        report["hashing"].append((str(p), None, "secure hashing library found (bcrypt/argon2/passlib)"))
    # Weak hashes
    for pat in WEAK_HASH_PATTERNS:
        for m in re.finditer(pat, txt, flags=re.IGNORECASE):
            ln = txt.count("\n", 0, m.start()) + 1
            report["hashing"].append((str(p), ln, f"weak hashing usage: {m.group(0)} (consider bcrypt/argon2)"))

def check_infinite_loops(p: Path):
    txt = read_text_robust(p)
    if not txt:
        return
    for m in re.finditer(INFINITE_LOOP_PATTERN, txt):
        ln = txt.count("\n", 0, m.start()) + 1
        following = "\n".join(txt.splitlines()[ln-1:ln+20])
        if "time.sleep" not in following:
            report["infinite_loops"].append((str(p), ln, "while True without nearby sleep"))

def batch_check(p: Path):
    txt = read_text_robust(p)
    if not txt:
        return
    if p.suffix.lower() in BATCH_EXTS:
        if "python" in txt.lower() and "%*" not in txt and "%1" not in txt:
            report["batch_issues"].append((str(p), None, "batch script may not forward args (missing %*)"))
    elif p.suffix.lower() in SHELL_EXTS:
        if "python" in txt.lower() and "$@" not in txt and "$*" not in txt:
            report["batch_issues"].append((str(p), None, "shell script may not forward args (missing \"$@\")"))

def simulation_hints(p: Path):
    txt = read_text_robust(p)
    if not txt:
        return
    for m in re.finditer(r"\bsimulate\b|\bSimulationManager\b|\bcheckpoint\b", txt, flags=re.IGNORECASE):
        ln = txt.count("\n", 0, m.start()) + 1
        report["simulation_hints"].append((str(p), ln, m.group(0)))

def model_dir_checks():
    candidates = [ROOT / "models", ROOT / "data" / "models", ROOT / "model"]
    for c in candidates:
        if c.exists() and c.is_dir():
            for child in c.iterdir():
                if child.is_dir():
                    found = any((child / fn).exists() for fn in MODEL_FILE_CANDIDATES)
                    if not found:
                        report["model_warnings"].append((str(child), "No recognized model files (config.json/pytorch_model.bin/*.safetensors)"))

def todo_checks(p: Path):
    txt = read_text_robust(p)
    if not txt:
        return
    for m in re.finditer(r"\bTODO\b|\bFIXME\b|\bXXX\b|\bHACK\b", txt):
        ln = txt.count("\n", 0, m.start()) + 1
        report["todos"].append((str(p), ln, m.group(0)))

def db_url_scan(p: Path):
    txt = read_text_robust(p)
    if not txt:
        return
    for pat in DB_URL_PATTERNS:
        for m in re.finditer(pat, txt, flags=re.IGNORECASE):
            ln = txt.count("\n", 0, m.start()) + 1
            capture = m.group(0)
            report["db_urls"].append((str(p), ln, capture[:300].replace("\n"," ")))

def run_all_checks():
    targets = list_targets()
    for p in targets:
        try:
            check_syntax(p)
            check_future(p)
            pattern_search(p, UNSAFE_PATTERNS, "unsafe")
            pattern_search(p, SECRET_PATTERNS, "secrets")
            db_url_scan(p)
            jwt_and_token_checks(p)
            hashing_checks(p)
            sql_risk_scan(p)
            check_infinite_loops(p)
            batch_check(p)
            simulation_hints(p)
            todo_checks(p)
        except Exception as e:
            print(f"Warning: scanning failed for {p}: {e}", file=sys.stderr)
    model_dir_checks()

def print_report():
    def section(name, items):
        print("\n" + "="*80)
        print(f"{name} ({len(items)})")
        print("-"*80)
        for i,it in enumerate(items[:500]):
            print(f"{i+1}: {it}")
    section("Syntax Errors", report["syntax_errors"])
    section("Misplaced __future__", report["bad_future"])
    section("Unsafe Patterns (eval/exec/pickle/yaml.load/subprocess...)", report["unsafe"])
    section("Hardcoded Secrets / Tokens", report["secrets"])
    section("DB URL patterns with credentials (heuristic)", report["db_urls"])
    section("JWT/Token heuristics", report["jwt"])
    section("Password hashing checks", report["hashing"])
    section("SQL Injection risk heuristics", report["sql_risk"])
    section("Infinite Loop Heuristics", report["infinite_loops"])
    section("Batch/Shell arg-forward issues", report["batch_issues"])
    section("Simulation / checkpoint hints", report["simulation_hints"])
    section("Model directory warnings", report["model_warnings"])
    section("TODO / FIXME / HACK markers", report["todos"])
    print("\n\nSummary Recommendations (short):")
    print("- Fix Syntax Errors first.")
    print("- Ensure 'from __future__' lines are at top of files that use them.")
    print("- Replace yaml.load with yaml.safe_load, remove eval/exec, avoid pickle.loads on untrusted data.")
    print("- Remove hardcoded secrets; use env vars or OS secrets manager; never commit keys.")
    print("- DB URLs containing credentials should be moved to env and use TLS (sslmode=require).")
    print("- Use bcrypt/argon2/passlib for password hashing; avoid raw hashlib for passwords.")
    print("- Ensure JWTs include 'exp' and use secure signing (HS256/RS256) and short expiries; avoid alg=none.")
    print("- Parameterize SQL queries, avoid f-strings / format / % into SQL; use DB library parameterization.")
    print("- Ensure batch scripts forward args correctly (Windows: %*; Bash: \"$@\" )")
    print("- For large simulation runs: use SimulationManager/ProcessPoolExecutor, checkpointing and disk backpressure.")
    print("- After you upload audit_output.txt I'll produce prioritized, PR-ready patches for the highest-risk items.")
    print("\nEnd of extended audit.")

if __name__ == "__main__":
    run_all_checks()
    print_report()