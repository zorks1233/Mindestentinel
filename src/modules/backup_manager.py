# src/modules/backup_manager.py
"""
BackupManager - erstellte sichere Snapshots der wichtigsten Verzeichnisse (data/, config/, models/)
Features:
- create_backup(archive_path, include_paths)
- list_backups(backup_dir)
- restore_backup(archive_path, target_dir)
- optional: encrypt/decrypt with cryptography.Fernet key (if provided)
"""

from __future__ import annotations
import time
import tarfile
import os
from pathlib import Path
import shutil
import tempfile
from typing import List, Optional, Dict, Any

try:
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False

class BackupManager:
    def __init__(self, base_dir: str | Path = "data", backup_dir: str | Path = "data/backups"):
        self.base_dir = Path(base_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, archive_name: Optional[str] = None, include_paths: Optional[List[str]] = None, encrypt_key: Optional[bytes] = None) -> Path:
        """
        Creates a tar.gz backup of include_paths (relative to project root or absolute).
        If include_paths is None, defaults to ['data', 'config'].
        If encrypt_key is provided and cryptography is available, the resulting .tar.gz will be encrypted to .enc
        Returns Path to created archive (or encrypted file).
        """
        include_paths = include_paths or ["data", "config"]
        ts = int(time.time() if hasattr(os, "time") else __import__("time").time())
        if archive_name:
            archive = Path(archive_name)
        else:
            archive = self.backup_dir / f"mindest_backup_{ts}.tar.gz"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")
        tmp.close()
        try:
            with tarfile.open(tmp.name, "w:gz") as tar:
                for p in include_paths:
                    path = Path(p)
                    if not path.exists():
                        continue
                    tar.add(str(path), arcname=str(path))
            # move tmp to final archive
            shutil.move(tmp.name, str(archive))
            # optional encryption
            if encrypt_key:
                if not _HAS_CRYPTO:
                    raise RuntimeError("cryptography required for encryption")
                f = Fernet(encrypt_key)
                data = archive.read_bytes()
                token = f.encrypt(data)
                enc_path = archive.with_suffix(archive.suffix + ".enc")
                enc_path.write_bytes(token)
                archive.unlink()
                return enc_path
            return archive
        finally:
            try:
                if Path(tmp.name).exists():
                    Path(tmp.name).unlink()
            except Exception:
                pass

    def list_backups(self) -> List[Path]:
        return sorted([p for p in self.backup_dir.iterdir() if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)

    def restore_backup(self, archive_path: str | Path, target_dir: Optional[str] = None, decrypt_key: Optional[bytes] = None) -> None:
        """
        Restores archive (tar.gz or encrypted .enc). If encrypted, decrypt_key is required.
        Restores files into target_dir (defaults to project root).
        """
        a = Path(archive_path)
        if not a.exists():
            raise FileNotFoundError(a)
        # handle encrypted file
        if a.suffix == ".enc":
            if not decrypt_key:
                raise ValueError("decrypt_key required for encrypted backup")
            if not _HAS_CRYPTO:
                raise RuntimeError("cryptography required to decrypt backup")
            f = Fernet(decrypt_key)
            token = a.read_bytes()
            data = f.decrypt(token)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz")
            try:
                tmp.write(data)
                tmp.flush()
                tmp.close()
                with tarfile.open(tmp.name, "r:gz") as tar:
                    tar.extractall(path=target_dir or ".")
            finally:
                try:
                    Path(tmp.name).unlink()
                except Exception:
                    pass
            return
        # not encrypted -> extract directly
        with tarfile.open(a, "r:gz") as tar:
            tar.extractall(path=target_dir or ".")
