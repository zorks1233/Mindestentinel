# src/api/auth_endpoints.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.core import auth as auth_core
from .token_auth import create_session_token, verify_session_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    username: str
    password: str
    totp: str | None = None
    backup_code: str | None = None

class LoginOut(BaseModel):
    token: str
    expires_in: int

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn):
    if not auth_core.verify_password(payload.username, payload.password):
        raise HTTPException(status_code=403, detail="Invalid credentials")
    user = auth_core.get_user(payload.username)
    # If user has totp configured, require either totp or backup_code
    if user and user.get("totp_secret"):
        if payload.totp:
            ok = auth_core.verify_totp(payload.username, payload.totp)
            if not ok:
                raise HTTPException(status_code=403, detail="Invalid TOTP token")
        elif payload.backup_code:
            ok = auth_core.verify_and_consume_backup_code(payload.username, payload.backup_code)
            if not ok:
                raise HTTPException(status_code=403, detail="Invalid backup code")
        else:
            raise HTTPException(status_code=400, detail="TOTP required for this account")
    token = create_session_token(payload.username, is_admin=user.get("is_admin", False) if user else False, expires_seconds=3600)
    return {"token": token, "expires_in": 3600}

def get_current_user(token: str = Depends(lambda authorization=Depends(lambda: None): None)):
    # placeholder for dependency injection; in real routing use header dependency
    raise NotImplementedError("Use dependency from src.api.rest_api or include router via create_app helper")
