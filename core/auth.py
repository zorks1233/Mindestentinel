"""
src/core/auth.py
User management with password hashing (PBKDF2), TOTP (pyotp optional) and backup codes.
Stores users in SQLite at data/users.db.
Provides CLI helpers to create users and verify TOTP/backup codes.
"""
from __future__ import annotations
import os
import sqlite3
import json
import hashlib
import hmac
import secrets
import time
from typing import Optional, List, Dict
from pathlib import Path

DB_PATH = Path("data") / "users.db"
PBKDF2_ITERS = 200_000
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 10

try:
    import pyotp  # type: ignore
    _HAS_PYOTP = True
except Exception:
    _HAS_PYOTP = False

def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        totp_secret TEXT,
        backup_codes TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at REAL
    )""")
    con.commit()
    return con

def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS)
    return dk.hex()

def create_user(username: str, password: str, is_admin: bool = False) -> Dict[str, str]:
    con = _ensure_db()
    cur = con.cursor()
    salt = secrets.token_bytes(16)
    phash = _hash_password(password, salt)
    totp_secret = None
    if _HAS_PYOTP:
        totp_secret = pyotp.random_base32()
    backup_codes = [_generate_backup_code() for _ in range(BACKUP_CODE_COUNT)]
    backup_json = json.dumps(backup_codes)
    now = time.time()
    cur.execute("INSERT INTO users (username, password_hash, salt, totp_secret, backup_codes, is_admin, created_at) VALUES (?,?,?,?,?,?,?)",
                (username, phash, salt.hex(), totp_secret, backup_json, 1 if is_admin else 0, now))
    con.commit()
    con.close()
    return {"username": username, "totp_secret": totp_secret, "backup_codes": backup_codes}

def _generate_backup_code() -> str:
    return secrets.token_urlsafe(8)

def verify_password(username: str, password: str) -> bool:
    con = _ensure_db()
    cur = con.cursor()
    cur.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    con.close()
    if not row:
        return False
    stored_hash, salt_hex = row
    salt = bytes.fromhex(salt_hex)
    return hmac.compare_digest(stored_hash, _hash_password(password, salt))

def get_user(username: str) -> Optional[Dict]:
    con = _ensure_db()
    cur = con.cursor()
    cur.execute("SELECT id, username, totp_secret, backup_codes, is_admin, created_at FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    uid, uname, totp_secret, backup_json, is_admin, created_at = row
    backup_codes = json.loads(backup_json) if backup_json else []
    return {"id": uid, "username": uname, "totp_secret": totp_secret, "backup_codes": backup_codes, "is_admin": bool(is_admin), "created_at": created_at}

def get_totp_uri(username: str) -> Optional[str]:
    user = get_user(username)
    if not user:
        return None
    if not _HAS_PYOTP:
        raise RuntimeError("pyotp not installed - install via pip install pyotp to enable TOTP")
    secret = user.get("totp_secret")
    if not secret:
        return None
    # issuer set to Mindestentinel
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="Mindestentinel")

def verify_totp(username: str, token: str) -> bool:
    if not _HAS_PYOTP:
        raise RuntimeError("pyotp not installed")
    user = get_user(username)
    if not user or not user.get("totp_secret"):
        return False
    totp = pyotp.TOTP(user["totp_secret"])
    return bool(totp.verify(token, valid_window=1))

def verify_and_consume_backup_code(username: str, code: str) -> bool:
    con = _ensure_db()
    cur = con.cursor()
    cur.execute("SELECT backup_codes FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        con.close()
        return False
    backup_json = row[0] or "[]"
    codes = json.loads(backup_json)
    if code in codes:
        codes.remove(code)
        cur.execute("UPDATE users SET backup_codes = ? WHERE username = ?", (json.dumps(codes), username))
        con.commit()
        con.close()
        return True
    con.close()
    return False

def regenerate_backup_codes(username: str) -> List[str]:
    con = _ensure_db()
    cur = con.cursor()
    new_codes = [_generate_backup_code() for _ in range(BACKUP_CODE_COUNT)]
    cur.execute("UPDATE users SET backup_codes = ? WHERE username = ?", (json.dumps(new_codes), username))
    con.commit()
    con.close()
    return new_codes

def list_users() -> List[Dict]:
    con = _ensure_db()
    cur = con.cursor()
    cur.execute("SELECT username, is_admin, created_at FROM users")
    rows = cur.fetchall()
    con.close()
    return [{"username": r[0], "is_admin": bool(r[1]), "created_at": r[2]} for r in rows]

if __name__ == '__main__':
    print("User manager: create users with create_user(username,password,is_admin=False)")
