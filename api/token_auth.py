# src/api/token_auth.py
"""
Simple stateless session tokens using HMAC-SHA256.
Provides create_session_token(username, is_admin, expires_seconds)
and verify_session_token(token) -> payload or raises.
No external deps required.
"""
from __future__ import annotations
import os, time, json, hmac, hashlib, base64
from typing import Optional, Dict

SECRET = os.getenv("SESSION_SECRET") or os.getenv("MIND_API_KEY") or "default_dev_secret_change_me"

def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _b64decode(data: str) -> bytes:
    rem = len(data) % 4
    if rem > 0:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("ascii"))

def create_session_token(username: str, is_admin: bool=False, expires_seconds: int=3600) -> str:
    header = {"alg":"HS256","typ":"TOKEN"}
    payload = {"user": username, "admin": bool(is_admin), "exp": int(time.time()) + int(expires_seconds)}
    header_b = _b64encode(json.dumps(header, separators=(",",":")).encode("utf-8"))
    payload_b = _b64encode(json.dumps(payload, separators=(",",":")).encode("utf-8"))
    signing_input = f"{header_b}.{payload_b}".encode("ascii")
    sig = hmac.new(SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b = _b64encode(sig)
    return f"{header_b}.{payload_b}.{sig_b}"

def verify_session_token(token: str) -> Dict:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token structure")
        header_b, payload_b, sig_b = parts
        signing_input = f"{header_b}.{payload_b}".encode("ascii")
        expected = hmac.new(SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
        sig = _b64decode(sig_b)
        if not hmac.compare_digest(expected, sig):
            raise ValueError("Invalid signature")
        payload_json = _b64decode(payload_b).decode("utf-8")
        payload = json.loads(payload_json)
        if "exp" in payload and int(time.time()) > int(payload["exp"]):
            raise ValueError("Token expired")
        return payload
    except Exception as e:
        raise ValueError("Invalid token: " + str(e))
