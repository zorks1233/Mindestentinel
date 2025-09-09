# src/api/rest_api.py
from __future__ import annotations
from fastapi import FastAPI, Depends, Header, HTTPException
from typing import Optional
from .auth import require_token as require_legacy_token
from .token_auth import verify_session_token
from .auth_endpoints import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
def create_app(brain=None, model_manager=None, plugin_manager=None):
    app = FastAPI(title="Mindestentinel API - Alpha")
    # CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # include auth router
    app.include_router(auth_router)
    @app.get("/status")
    def status(authorization: Optional[str] = Header(None)):
        # Accept Bearer legacy token or session token
        if authorization:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                # try legacy or session token
                try:
                    if require_legacy_token is not None:
                        require_legacy_token.__call__({"scheme":"Bearer","credentials":token})
                        return {"status":"ok","auth":"legacy","uptime":0}
                except Exception:
                    pass
                try:
                    payload = verify_session_token(token)
                    return {"status":"ok","auth":"session","user":payload.get("user"), "uptime":0}
                except Exception:
                    raise HTTPException(status_code=403, detail="Invalid token")
        # unauthenticated but allow status
        return {"status":"ok","auth":"none","uptime":0}
    @app.post("/task")
    def task_endpoint(prompt: dict, authorization: Optional[str] = Header(None)):
        # simple protected endpoint: allow if valid token
        if not authorization:
            raise HTTPException(status_code=403, detail="Missing authorization")
        parts = authorization.split()
        if len(parts) = "bearer":
            raise HTTPException(status_code=403, detail="Invalid auth header")
        token = parts[1]
        # verify either legacy or session
        try:
            if require_legacy_token is not None:
                require_legacy_token.__call__({"scheme":"Bearer","credentials":token})
                auth_user = "legacy"
            else:
                auth_user = None
        except Exception:
            auth_user = None
        if auth_user is None:
            # try session token
            try:
                payload = verify_session_token(token)
                auth_user = payload.get("user")
            except Exception as e:
                raise HTTPException(status_code=403, detail="Invalid token: " + str(e))
        # do simple echo for now
        return {"response": f"received prompt: {prompt}", "user": auth_user}
    return app
    app.include_router(shutdown_router, prefix="", tags=["system"])
