# src/core/auth.py
"""
Auth helper for Mindestentinel.

Provides:
- init_db(db_path)
- create_user(username, password, is_admin=False)
- get_user(username)
- verify_password(username, password)
- set_password(username, new_password)
- delete_user(username)
- list_users()
- generate_totp_secret()
- verify_totp(username, token)
- generate_backup_codes(n=8)
"""

from __future__ import annotations
import sqlite3
import os
import json
import time
import logging
import secrets
import hashlib
from typing import Optional, Dict, Any, List

log = logging.getLogger("mindestentinel.auth")
# default DB path relative to project root
DEFAULT_DB_PATH = os.environ.get("MINDEST_DB_PATH", os.path.join("data", "database.sqlite3"))

# PBKDF2 config
PBKDF2_ALGO = "sha256"
PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
HASH_BYTES = 32


# Optional TOTP support (pyotp). If not installed, TOTP functions will be disabled gracefully.
try:
    import pyotp  # type: ignore
    HAS_PYOTP = True
except Exception:
    HAS_PYOTP = False
    log.debug("pyotp not available: TOTP functions will be disabled.")


class UserExists(Exception):
    pass


class UserNotFound(Exception):
    pass


def _ensure_db_dir(db_path: str):
    directory = os.path.dirname(db_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return sqlite3.Connection and ensure schema exists."""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    _ensure_db_dir(db_path)
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection):
    """Creates users table if not exists."""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          salt TEXT NOT NULL,
          totp_secret TEXT,
          backup_codes TEXT,
          is_admin INTEGER DEFAULT 0,
          created_at REAL,
          last_login REAL
        )
        """
    )
    conn.commit()


def _pbkdf2_hash(password: str, salt: bytes) -> str:
    """Return hex string of PBKDF2-HMAC."""
    dk = hashlib.pbkdf2_hmac(PBKDF2_ALGO, password.encode("utf-8"), salt, PBKDF2_ITERATIONS, dklen=HASH_BYTES)
    return dk.hex()


def generate_salt() -> bytes:
    return secrets.token_bytes(SALT_BYTES)


def generate_totp_secret() -> Optional[str]:
    if not HAS_PYOTP:
        return None
    return pyotp.random_base32()


def generate_backup_codes(n: int = 8) -> List[str]:
    codes = []
    for _ in range(n):
        codes.append(secrets.token_hex(6))  # 12 hex chars ≈ usable code
    return codes


def create_user(username: str, password: str, is_admin: bool = False, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a user. If user already exists, returns the existing user info (no exception).
    Returns a dict with user info (without password_hash).
    """
    username = username.strip()
    if not username:
        raise ValueError("username must not be empty")
    if not password:
        raise ValueError("password must not be empty")

    conn = get_connection(db_path)
    cur = conn.cursor()

    # if user exists -> return existing
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if row:
        log.info("create_user: username '%s' already exists; returning existing user.", username)
        return {
            "id": row["id"],
            "username": row["username"],
            "is_admin": bool(row["is_admin"]),
            "created_at": row["created_at"],
            "already_exists": True,
        }

    salt = generate_salt()
    phash = _pbkdf2_hash(password, salt)
    totp_secret = generate_totp_secret()
    backup_codes = generate_backup_codes()
    backup_json = json.dumps(backup_codes)
    now = time.time()

    cur.execute(
        "INSERT INTO users (username, password_hash, salt, totp_secret, backup_codes, is_admin, created_at) VALUES (?,?,?,?,?,?,?)",
        (username, phash, salt.hex(), totp_secret, backup_json, 1 if is_admin else 0, now),
    )
    conn.commit()
    user_id = cur.lastrowid
    log.info("create_user: created user '%s' (id=%s)", username, user_id)
    return {
        "id": user_id,
        "username": username,
        "is_admin": bool(is_admin),
        "created_at": now,
        "totp_secret": totp_secret,
        "backup_codes": backup_codes,
        "already_exists": False,
    }


def get_user(username: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        return None
    data = dict(row)
    # convert json
    if data.get("backup_codes"):
        try:
            data["backup_codes"] = json.loads(data["backup_codes"])
        except Exception:
            data["backup_codes"] = []
    data["is_admin"] = bool(data.get("is_admin"))
    return data


def verify_password(username: str, password: str, db_path: Optional[str] = None) -> bool:
    user = get_user(username, db_path)
    if not user:
        return False
    salt = bytes.fromhex(user["salt"])
    expected = user["password_hash"]
    phash = _pbkdf2_hash(password, salt)
    return secrets.compare_digest(phash, expected)


def set_password(username: str, new_password: str, db_path: Optional[str] = None) -> bool:
    if not new_password:
        raise ValueError("new_password must not be empty")
    user = get_user(username, db_path)
    if not user:
        raise UserNotFound(username)
    conn = get_connection(db_path)
    cur = conn.cursor()
    salt = generate_salt()
    phash = _pbkdf2_hash(new_password, salt)
    cur.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?", (phash, salt.hex(), username))
    conn.commit()
    log.info("set_password: password updated for %s", username)
    return True


def delete_user(username: str, db_path: Optional[str] = None) -> bool:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = ?", (username,))
    changed = cur.rowcount
    conn.commit()
    log.info("delete_user: deleted %s -> rows=%s", username, changed)
    return changed > 0


def list_users(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT id, username, is_admin, created_at, last_login FROM users ORDER BY id")
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def touch_last_login(username: str, db_path: Optional[str] = None):
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = time.time()
    cur.execute("UPDATE users SET last_login = ? WHERE username = ?", (now, username))
    conn.commit()


def verify_totp(username: str, token: str, db_path: Optional[str] = None) -> bool:
    if not HAS_PYOTP:
        log.warning("verify_totp called but pyotp not installed")
        return False
    user = get_user(username, db_path)
    if not user:
        return False
    totp_secret = user.get("totp_secret")
    if not totp_secret:
        return False
    totp = pyotp.TOTP(totp_secret)
    return totp.verify(token, valid_window=1)


# Utility: delete database (careful)
def _drop_database(db_path: Optional[str] = None):
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    if os.path.exists(db_path):
        os.remove(db_path)
        log.warning("Removed DB at %s", db_path)
