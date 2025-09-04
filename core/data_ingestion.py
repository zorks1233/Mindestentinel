# data_ingestion 
# src/core/data_ingestion.py
"""
DataIngestion - sichere Speicherung von Uploads, dedup via sha256, simple metadata extraction.
- API:
    save_text(name, text) -> dict
    save_file(src_path) -> dict
    save_bytes(bytes, name) -> dict
    get_metadata(path) -> dict
"""

from __future__ import annotations
import time
import hashlib
from pathlib import Path
import os
import json
from typing import Dict, Any

BASE_UPLOAD_DIR = Path("data") / "uploads"

class DataIngestion:
    def __init__(self, base_dir: str | None = None):
        self.base = Path(base_dir) if base_dir else BASE_UPLOAD_DIR
        self.text_dir = self.base / "texts"
        self.file_dir = self.base / "files"
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self.file_dir.mkdir(parents=True, exist_ok=True)

    def _hash_bytes(self, data: bytes) -> str:
        h = hashlib.sha256()
        h.update(data)
        return h.hexdigest()

    def save_text(self, name: str, text: str) -> Dict[str,Any]:
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", ".", "_", "-")).rstrip()
        filename = f"{safe_name}_{hashlib.sha1(text.encode('utf-8')).hexdigest()[:8]}.txt"
        path = self.text_dir / filename
        with path.open("w", encoding="utf-8") as fh:
            fh.write(text)
        meta = {"path": str(path), "size": path.stat().st_size}
        # write metadata file
        with (path.with_suffix(".meta.json")).open("w", encoding="utf-8") as mfh:
            json.dump({"name": name, "ts": int(time.time()) if hasattr(os, "time") else 0}, mfh)
        return meta

    def save_file(self, src_path: str) -> Dict[str,Any]:
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(src_path)
        data = src.read_bytes()
        h = self._hash_bytes(data)
        dst = self.file_dir / (h + src.suffix)
        if not dst.exists():
            dst.write_bytes(data)
        meta = {"path": str(dst), "sha256": h, "orig_name": src.name, "size": dst.stat().st_size}
        return meta

    def save_bytes(self, b: bytes, name: str = "blob") -> Dict[str,Any]:
        h = self._hash_bytes(b)
        ext = Path(name).suffix or ""
        dst = self.file_dir / (h + ext)
        if not dst.exists():
            dst.write_bytes(b)
        return {"path": str(dst), "sha256": h, "size": dst.stat().st_size}

    def get_metadata(self, path: str) -> Dict[str,Any]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        stat = p.stat()
        return {"path": str(p), "size": stat.st_size, "mtime": int(stat.st_mtime)}
