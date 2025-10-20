# src/core/dependencies.py
import importlib
from typing import Dict, List, Tuple

REQUIRED_DEPS = {
    "core": ["fastapi", "uvicorn", "pydantic", "pyyaml"],
    "ml": ["torch", "transformers"],
    "database": ["sqlite3"],
}
OPTIONAL_DEPS = {
    "audio": ["soundfile", "webrtcvad"],
    "vision": ["PIL", "cv2"],
}

def check_dependencies() -> Tuple[Dict[str,bool], List[str]]:
    status = {}
    missing_required = []
    for category, deps in REQUIRED_DEPS.items():
        for dep in deps:
            try:
                importlib.import_module(dep)
                status[dep] = True
            except Exception:
                status[dep] = False
                missing_required.append(dep)
    for category, deps in OPTIONAL_DEPS.items():
        for dep in deps:
            try:
                importlib.import_module(dep)
                status[dep] = True
            except Exception:
                status[dep] = False
    return status, missing_required
