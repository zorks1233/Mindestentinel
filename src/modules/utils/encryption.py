# src/modules/utils/encryption.py
"""
Encryption helpers using cryptography.Fernet (symmetric encryption).
Provides: generate_key, load_key_from_file, encrypt_bytes, decrypt_bytes, encrypt_file, decrypt_file.

Dependency: cryptography
Install: pip install cryptography
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Tuple
try:
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except Exception:
    _HAS_CRYPTO = False

def generate_key() -> bytes:
    if not _HAS_CRYPTO:
        raise RuntimeError("cryptography fehlt. pip install cryptography")
    return Fernet.generate_key()

def save_key(key: bytes, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(key)

def load_key(path: str) -> bytes:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return p.read_bytes()

def encrypt_bytes(data: bytes, key: bytes) -> bytes:
    if not _HAS_CRYPTO:
        raise RuntimeError("cryptography fehlt. pip install cryptography")
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_bytes(token: bytes, key: bytes) -> bytes:
    if not _HAS_CRYPTO:
        raise RuntimeError("cryptography fehlt. pip install cryptography")
    f = Fernet(key)
    return f.decrypt(token)

def encrypt_file(src_path: str, dst_path: str, key: bytes) -> None:
    data = Path(src_path).read_bytes()
    enc = encrypt_bytes(data, key)
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    Path(dst_path).write_bytes(enc)

def decrypt_file(src_path: str, dst_path: str, key: bytes) -> None:
    token = Path(src_path).read_bytes()
    dec = decrypt_bytes(token, key)
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    Path(dst_path).write_bytes(dec)
