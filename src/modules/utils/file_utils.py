# file utils 
# src/modules/utils/file_utils.py
"""
File utilities: sichere, atomare Schreib-/Leseoperationen, Aufräum-Helpers.
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import List, Optional
import tempfile

def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def atomic_write_bytes(path: str, data: bytes, mode: str = "wb") -> None:
    dest = Path(path)
    ensure_dir(str(dest.parent))
    # write to temp file then move
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent))
    try:
        with os.fdopen(fd, mode) as f:
            f.write(data)
        os.replace(tmp, str(dest))
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass

def atomic_write_text(path: str, text: str, encoding: str = "utf-8") -> None:
    atomic_write_bytes(path, text.encode(encoding))

def read_text(path: str, encoding: str = "utf-8") -> str:
    with open(path, "r", encoding=encoding) as f:
        return f.read()

def read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def safe_remove(path: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return True
    except Exception:
        return False

def copy_file(src: str, dst: str, overwrite: bool = False) -> str:
    s = Path(src)
    d = Path(dst)
    ensure_dir(str(d.parent))
    if d.exists() and not overwrite:
        raise FileExistsError(f"Destination exists: {dst}")
    shutil.copy2(s, d)
    return str(d)

def list_files(path: str, glob: Optional[str] = None) -> List[str]:
    p = Path(path)
    if not p.exists():
        return []
    if glob:
        return [str(x) for x in p.glob(glob)]
    return [str(x) for x in p.iterdir()]
