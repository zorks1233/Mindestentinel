# src/api/auth.py
"""
API auth helpers for Mindestentinel.

Provides:
 - _get_expected_key() -> optional legacy key (MIND_API_KEY)
 - LegacyTokenChecker class instance `require_legacy_token` with a .__call__ helper
   so older code that does require_legacy_token.__call__({...}) still works.
 - require_token dependency for FastAPI endpoints: accepts either the legacy key
   or a session token verified by `src.api.token_auth.verify_session_token` (if available).

This module is intentionally conservative: dotenv usage is optional and only attempted
if python-dotenv is installed. No secrets are stored in the repository.
"""
from __future__ import annotations
import os
from typing import Optional, Any, Dict

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Try to import token-based session verifier (may not be present in older builds)
try:
    from .token_auth import verify_session_token  # type: ignore
except Exception:
    verify_session_token = None  # type: ignore

# Try to support reading .env if python-dotenv is installed
try:
    from dotenv import find_dotenv, load_dotenv  # type: ignore
except Exception:
    find_dotenv = None  # type: ignore
    load_dotenv = None  # type: ignore

# Load LEGACY_KEY at import time if possible (fallback defers to env lookup)
LEGACY_KEY: Optional[str] = None
try:
    # Prefer explicit env var first
    LEGACY_KEY = os.environ.get("MIND_API_KEY")
    # If not present and python-dotenv available, try loading .env
    if not LEGACY_KEY and find_dotenv and load_dotenv:
        dotenv_path = find_dotenv(raise_error_if_not_found=False)
        if dotenv_path:
            load_dotenv(dotenv_path)
            LEGACY_KEY = os.environ.get("MIND_API_KEY")
except Exception:
    LEGACY_KEY = None


def _get_expected_key() -> Optional[str]:
    """
    Return the expected legacy API key (MIND_API_KEY).

    Order of checking:
      1. In-memory LEGACY_KEY (loaded at import)
      2. environment variable MIND_API_KEY
      3. attempt to load .env via python-dotenv if available
      4. None if not found
    """
    global LEGACY_KEY
    if LEGACY_KEY:
        return LEGACY_KEY

    # 1) environment
    try:
        key = os.getenv("MIND_API_KEY")
        if key:
            LEGACY_KEY = key
            return key
    except Exception:
        pass

    # 2) try .env (optional)
    try:
        if find_dotenv and load_dotenv:
            dotenv_path = find_dotenv(raise_error_if_not_found=False)
            if dotenv_path:
                load_dotenv(dotenv_path)
                key = os.getenv("MIND_API_KEY")
                if key:
                    LEGACY_KEY = key
                    return key
    except Exception:
        pass

    return None


def _is_valid_legacy_token(token: Optional[str]) -> bool:
    """
    Quick check whether the provided token matches the legacy API key.
    """
    if not token:
        return False
    expected = _get_expected_key()
    if not expected:
        return False
    return token == expected


class LegacyTokenChecker:
    """
    Compatibility helper that can be used as a dependency or callable object.

    Behavior:
      - Can be called with:
         * fastapi.security.HTTPAuthorizationCredentials
         * dict-like {"scheme": "...", "credentials": "..."} (some code uses this)
         * raw token string
      - Raises HTTPException(403) on failure.
      - Returns True on success.
    """

    def __call__(self, credentials: Any) -> bool:
        # Accept HTTPAuthorizationCredentials
        token: Optional[str] = None

        # If FastAPI passed HTTPAuthorizationCredentials
        if isinstance(credentials, HTTPAuthorizationCredentials):
            token = credentials.credentials
        # If other frameworks / code passed a dict-like object
        elif isinstance(credentials, dict):
            token = credentials.get("credentials") or credentials.get("token") or credentials.get("key")
        # If a plain string was passed
        elif isinstance(credentials, str):
            token = credentials
        # If None or unknown type
        else:
            # try to be permissive: maybe passed object has 'credentials' attr
            try:
                token = getattr(credentials, "credentials", None)
            except Exception:
                token = None

        if _is_valid_legacy_token(token):
            return True

        # not matching legacy -> raise
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid legacy API key")


# provide instance (so older code expecting require_legacy_token.__call__ works)
require_legacy_token = LegacyTokenChecker()

# FastAPI dependency: accepts either legacy key or session token (preferred)
bearer_scheme = HTTPBearer(auto_error=False)


def require_token(credentials: Optional[HTTPAuthorizationCredentials] = None) -> Dict[str, Any]:
    """
    FastAPI dependency to require authorization.

    It accepts:
      - Legacy API key: exact match to MIND_API_KEY (returns {"auth":"legacy"})
      - Session token (HMAC token created by src.api.token_auth): returns {"auth":"session","payload":...}

    Usage in endpoints:
        user = Depends(require_token)

    If both missing or invalid -> raises HTTPException(403).
    """
    # If the dependency was used with Depends(HTTPBearer()), callers will get an HTTPAuthorizationCredentials
    # But sometimes this dependency might be called directly; accept None.
    token = None
    if isinstance(credentials, HTTPAuthorizationCredentials):
        token = credentials.credentials
    elif isinstance(credentials, dict):
        token = credentials.get("credentials") or credentials.get("token")
    elif isinstance(credentials, str):
        token = credentials

    # 1) check legacy
    if _is_valid_legacy_token(token):
        return {"auth": "legacy"}

    # 2) try session token verifier (if available)
    if verify_session_token is not None:
        try:
            payload = verify_session_token(token)
            return {"auth": "session", "payload": payload}
        except Exception:
            # fall through to error
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid session token")

    # no valid auth method
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing or invalid authorization")


# Short helper for direct checks in other modules
def check_bearer_token_header(authorization_header: Optional[str]) -> bool:
    """
    Utility: given an Authorization header string like "Bearer <token>", validate it (legacy or session).
    Returns True when valid, False otherwise.
    """
    if not authorization_header:
        return False
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    token = parts[1]
    # legacy
    if _is_valid_legacy_token(token):
        return True
    # session
    if verify_session_token is not None:
        try:
            verify_session_token(token)
            return True
        except Exception:
            return False
    return False
