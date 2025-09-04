# api utils 
# src/api/api_utils.py
from __future__ import annotations
import os
from pathlib import Path
from fastapi import UploadFile
from typing import Dict, Any

BASE_UPLOAD_DIR = Path("data") / "uploads"
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def save_upload_file(upload_file: UploadFile, subdir: str = "files") -> Dict[str, Any]:
    sub = BASE_UPLOAD_DIR / subdir
    sub.mkdir(parents=True, exist_ok=True)
    dest = sub / upload_file.filename
    # write to disk
    with dest.open("wb") as f:
        content = await upload_file.read()
        f.write(content)
    return {"path": str(dest), "filename": upload_file.filename, "content_type": upload_file.content_type, "size": dest.stat().st_size}
