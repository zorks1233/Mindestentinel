# src/api/rest_api.py
"""
rest_api.py - REST API für Mindestentinel

Diese Datei implementiert die REST API des Systems.
"""

import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, Any, Optional

logger = logging.getLogger("mindestentinel.api.rest")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_app(
    brain,
    model_manager,
    plugin_manager,
    rule_engine=None,
    user_manager=None,
    auth_manager=None
):
    """Erstellt die FastAPI-App
    
    Args:
        brain: AIBrain-Instanz
        model_manager: ModelManager-Instanz
        plugin_manager: PluginManager-Instanz
        rule_engine: RuleEngine-Instanz (optional)
        user_manager: UserManager-Instanz (optional)
        auth_manager: AuthManager-Instanz (optional)
    
    Returns:
        FastAPI: Die erstellte FastAPI-App
    """
    app = FastAPI()
    
    # Speichere Komponenten im App-State
    app.state.brain = brain
    app.state.model_manager = model_manager
    app.state.plugin_manager = plugin_manager
    app.state.rule_engine = rule_engine
    app.state.user_manager = user_manager
    app.state.auth_manager = auth_manager
    
    @app.get("/")
    async def root():
        """Root-Endpoint"""
        return {"message": "Mindestentinel API is running"}
    
    @app.post("/token")
    async def login(username: str, password: str):
        """Login-Endpoint für Token-Erstellung"""
        logger.info(f"Loginversuch für Benutzer: {username}")
        
        if not auth_manager:
            logger.error("AuthManager nicht verfügbar")
            raise HTTPException(
                status_code=500,
                detail="Authentifizierungssystem nicht verfügbar"
            )
        
        try:
            user = auth_manager.authenticate_user(username, password)
            if not user:
                logger.warning(f"Ungültige Anmeldeversuche für Benutzer: {username}")
                raise HTTPException(
                    status_code=401,
                    detail="Ungültiger Benutzername oder Passwort"
                )
            
            access_token = auth_manager.create_access_token(
                username=user["username"],
                is_admin=user["is_admin"]
            )
            
            logger.info(f"Login erfolgreich für Benutzer: {username}")
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 1800,
                "is_admin": user["is_admin"]
            }
        except Exception as e:
            logger.error(f"Fehler bei der Anmeldung: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Interner Authentifizierungsfehler"
            )
    
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        """Holt den aktuellen Benutzer aus dem Token"""
        if not auth_manager:
            logger.error("AuthManager nicht verfügbar")
            raise HTTPException(
                status_code=500,
                detail="Authentifizierungssystem nicht verfügbar"
            )
        
        try:
            return auth_manager.verify_token(token)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei der Benutzerabfrage: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Interner Authentifizierungsfehler"
            )
    
    @app.post("/query")
    async def query(request: Request, current_user: Dict = Depends(get_current_user)):
        """Query-Endpoint für Benutzeranfragen"""
        data = await request.json()
        prompt = data.get("prompt", "")
        max_tokens = data.get("max_tokens", 512)
        
        logger.info(f"Abfrage von {current_user['sub']}: {prompt[:50]}...")
        
        if not prompt:
            raise HTTPException(
                status_code=400,
                detail="Prompt darf nicht leer sein"
            )
        
        try:
            responses = brain.query(prompt, max_tokens=max_tokens)
            return responses
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Fehler bei der Verarbeitung der Anfrage"
            )
    
    @app.get("/users")
    async def get_users(current_user: Dict = Depends(get_current_user)):
        """Endpoint zum Abrufen aller Benutzer (nur für Admins)"""
        if not current_user.get("is_admin", False):
            logger.warning(f"Zugriffsversuch auf Benutzerendpunkt durch Nicht-Admin: {current_user.get('sub')}")
            raise HTTPException(
                status_code=403,
                detail="Admin-Rechte erforderlich"
            )
        
        if not user_manager:
            logger.error("UserManager nicht verfügbar")
            raise HTTPException(
                status_code=500,
                detail="Benutzermanagementsystem nicht verfügbar"
            )
        
        try:
            users = user_manager.list_users()
            logger.info(f"{len(users)} Benutzer gefunden")
            return {"users": users}
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Benutzer: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Fehler beim Abrufen der Benutzer"
            )
    
    @app.get("/status")
    async def get_status(current_user: Dict = Depends(get_current_user)):
        """Endpoint zum Abrufen des Systemstatus"""
        try:
            status = brain.get_system_status()
            return status
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Systemstatus: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Fehler beim Abrufen des Systemstatus"
            )
    
    logger.info("REST API erfolgreich initialisiert")
    return app