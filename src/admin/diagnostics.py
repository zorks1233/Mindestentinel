# diagnostics 
# src/admin/diagnostics.py
"""
Diagnostics helpers: perform quick healthchecks:
- DB files writable
- data directories exist and writable
- required env vars (MIND_API_KEY) present (optional)
- optional deps: torch, transformers, faiss, qiskit, pennylane
"""

from __future__ import annotations
import os
import importlib
from pathlib import Path
from typing import Dict, Any

CHECK_DIRS = [
    Path("data"),
    Path("data/models"),
    Path("data/knowledge"),
    Path("logs")
]

OPTIONAL_MODULES = [
    ("torch", "torch"),
    ("transformers", "transformers"),
    ("faiss", "faiss"),
    ("qiskit", "qiskit"),
    ("pennylane", "pennylane"),
    ("zstandard", "zstandard"),
    ("psutil", "psutil"),
    ("pillow", "PIL"),
]

def run_diagnostics() -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    # directories
    dir_checks = {}
    for d in CHECK_DIRS:
        try:
            d.mkdir(parents=True, exist_ok=True)
            writable = os.access(d, os.W_OK)
            dir_checks[str(d)] = {"exists": d.exists(), "writable": writable}
        except Exception as e:
            dir_checks[str(d)] = {"exists": False, "error": str(e)}
    result["dirs"] = dir_checks

    # env
    result["env"] = {"MIND_API_KEY_set": bool(os.getenv("MIND_API_KEY"))}

    # optional modules
    mods = {}
    for name, import_name in OPTIONAL_MODULES:
        try:
            importlib.import_module(import_name)
            mods[name] = True
        except Exception:
            mods[name] = False
    result["optional_modules"] = mods

    # quick DB checks (knowledge DB)
    kb_path = Path("data") / "knowledge" / "kb.sqlite3"
    result["kb_db_exists"] = kb_path.exists()
    try:
        # attempt simple write
        with (Path("logs") / "diagnostics.tmp").open("w") as f:
            f.write("ok")
        os.remove(Path("logs") / "diagnostics.tmp")
        result["logs_writable"] = True
    except Exception:
        result["logs_writable"] = False

    return result
