# src/api/rest_api.py
"""
REST API für Mindestentinel

Diese Datei implementiert die REST API für das System.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

from src.core.ai_engine import AIBrain
from src.core.model_manager import ModelManager
# KORRIGIERT: plugin_manager ist in modules, nicht in core
from src.modules.plugin_manager import PluginManager
from src.core.auth_manager import AuthManager
from src.core.user_manager import UserManager

logger = logging.getLogger("mindestentinel.api.rest")

# FastAPI-App
app = FastAPI(
    title="Mindestentinel REST API",
    description="API für das autonome KI-System Mindestentinel",
    version="1.0.0"
)

# OAuth2-Schema für Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class QueryRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = 512

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    is_admin: bool

class ModelInfoResponse(BaseModel):
    name: str
    type: str
    status: str
    config: Dict[str, Any]
    categories: List[str]
    meta: Dict[str, Any]

class ModelListResponse(BaseModel):
    models: List[str]
    details: List[ModelInfoResponse]

class StatusResponse(BaseModel):
    status: str
    message: str
    version: str
    user: str
    is_admin: bool
    timestamp: str

class UserResponse(BaseModel):
    username: str
    is_admin: bool
    created_at: str

class UserListResponse(BaseModel):
    users: List[UserResponse]

def get_auth_manager():
    """Holt den AuthManager aus der App-Instanz"""
    return app.state.auth_manager

def get_model_manager():
    """Holt den ModelManager aus der App-Instanz"""
    return app.state.model_manager

def get_brain():
    """Holt das AIBrain aus der App-Instanz"""
    return app.state.brain

def get_user_manager():
    """Holt den UserManager aus der App-Instanz"""
    return app.state.user_manager

async def get_current_user(token: str = Depends(oauth2_scheme), auth_manager: AuthManager = Depends(get_auth_manager)):
    """Holt den aktuellen Benutzer aus dem Token"""
    try:
        return auth_manager.get_current_user(token)
    except HTTPException as e:
        logger.warning(f"Token-Verifikation fehlgeschlagen: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unerwarteter Fehler bei der Benutzerabfrage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Interner Authentifizierungsfehler"
        )

@app.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: TokenRequest,
    auth_manager: AuthManager = Depends(get_auth_manager),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Generiert ein Zugriffstoken für einen Benutzer"""
    logger.info(f"Loginversuch für Benutzer: {request.username}")
    
    user = auth_manager.authenticate_user(request.username, request.password)
    if not user:
        logger.warning(f"Login fehlgeschlagen für Benutzer: {request.username}")
        raise HTTPException(
            status_code=401,
            detail="Falscher Benutzername oder Passwort"
        )
    
    access_token = auth_manager.create_access_token(
        user["username"],
        user["is_admin"]
    )
    
    logger.info(f"Login erfolgreich für Benutzer: {request.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "is_admin": user["is_admin"]
    }

@app.get("/status", response_model=StatusResponse)
async def get_status(
    current_user: dict = Depends(get_current_user),
    brain: AIBrain = Depends(get_brain)
):
    """Gibt den aktuellen Status des Systems zurück"""
    logger.info(f"Statusabfrage von {current_user['username']}")
    
    return {
        "status": "running",
        "message": "Mindestentinel REST API ist aktiv",
        "version": "1.0.0",
        "user": current_user["username"],
        "is_admin": current_user["is_admin"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/models", response_model=ModelListResponse)
async def list_models(
    current_user: dict = Depends(get_current_user),
    model_manager: ModelManager = Depends(get_model_manager)
):
    """Listet alle verfügbaren Modelle auf"""
    logger.info(f"Modellabfrage von {current_user['username']}")
    
    try:
        model_names = model_manager.list_models()
        details = []
        
        for model_name in model_names:
            # Verwende get_model_config statt get_model_info
            config = model_manager.get_model_config(model_name)
            metadata = model_manager.get_model_metadata(model_name)
            
            details.append({
                "name": model_name,
                "type": config.get("type", "unknown"),
                "status": "loaded" if model_manager.is_model_loaded(model_name) else "unloaded",
                "config": config,
                "categories": metadata.get("categories", []),
                "meta": {
                    "last_improved": metadata.get("last_improved", None),
                    "performance_gain": metadata.get("performance_gain", 0.0)
                }
            })
        
        return {
            "models": model_names,
            "details": details
        }
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Modelle: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Abrufen der Modellinformationen"
        )

@app.post("/query", response_model=Dict[str, str])
async def query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
    brain: AIBrain = Depends(get_brain)
):
    """Verarbeitet eine Benutzerabfrage"""
    logger.info(f"Abfrage von {current_user['username']}: {request.prompt}...")
    
    try:
        responses = brain.query(
            request.prompt,
            max_tokens=request.max_tokens
        )
        return responses
    except Exception as e:
        logger.error(f"Fehler bei der Abfrage: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler bei der Verarbeitung der Anfrage"
        )

@app.get("/users", response_model=UserListResponse)
async def list_users(
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Listet alle Benutzer auf (nur für Admins)"""
    logger.info(f"Benutzerabfrage von {current_user['username']}")
    
    # Überprüfe Admin-Rechte
    if not current_user.get("is_admin", False):
        logger.warning(f"Zugriffsversuch auf Benutzerliste durch Nicht-Admin: {current_user['username']}")
        raise HTTPException(
            status_code=403,
            detail="Admin-Rechte erforderlich"
        )
    
    try:
        users = user_manager.list_users()
        return {"users": users}
    except Exception as e:
        logger.error(f"Fehler bei der Benutzerauflistung: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Abrufen der Benutzerliste"
        )

def create_app(brain: AIBrain, model_manager: ModelManager, plugin_manager: PluginManager, auth_manager: AuthManager):
    """Erstellt die FastAPI-App mit allen Abhängigkeiten"""
    app.state.brain = brain
    app.state.model_manager = model_manager
    app.state.plugin_manager = plugin_manager
    app.state.auth_manager = auth_manager
    app.state.user_manager = auth_manager.user_manager
    
    logger.info("REST API erfolgreich initialisiert")
    return app