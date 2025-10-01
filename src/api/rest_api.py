# src/api/rest_api.py
"""
rest_api.py - REST API für Mindestentinel

Diese Datei implementiert die REST API für das System.
Es ermöglicht den Zugriff auf die Funktionalitäten über HTTP.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
import time
from src.core.token_utils import decode_token, JWTError
from src.core.config import REQUIRE_2FA

logger = logging.getLogger("mindestentinel.rest_api")

# OAuth2-Schema für die Authentifizierung
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_app(ai_engine, model_manager, plugin_manager, auth_manager=None):
    """
    Erstellt die REST API.
    
    Args:
        ai_engine: Die AIBrain-Instanz
        model_manager: Der ModelManager
        plugin_manager: Der PluginManager
        auth_manager: Der AuthManager (optional)
        
    Returns:
        FastAPI: Die REST API
    """
    app = FastAPI(
        title="Mindestentinel API",
        description="API für das autonome KI-System Mindestentinel",
        version="1.0.0"
    )
    
    # Sicherstellen, dass alle erforderlichen Komponenten vorhanden sind
    if not ai_engine:
        raise ValueError("AIBrain ist erforderlich")
    if not model_manager:
        raise ValueError("ModelManager ist erforderlich")
    if not plugin_manager:
        raise ValueError("PluginManager ist erforderlich")
    
    # Dependency für die Authentifizierung (nur wenn AuthManager vorhanden)
    if auth_manager:
        def get_current_user(token: str = Depends(oauth2_scheme)):
            # Verifiziere das Token
            try:
                payload = decode_token(token)
                return {
                    "username": payload.get("username"),
                    "is_admin": payload.get("is_admin", False)
                }
            except JWTError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=str(e),
                    headers={"WWW-Authenticate": "Bearer"},
                )
    else:
        # Dummy-Authentifizierung, wenn kein AuthManager vorhanden
        def get_current_user():
            return {"username": "admin", "is_admin": True}
    
    @app.get("/")
    async def root():
        """Root-Endpoint der API."""
        return {
            "status": "running",
            "message": "Mindestentinel REST API ist aktiv",
            "version": "1.0.0",
            "auth_required": auth_manager is not None
        }
    
    if auth_manager:
        @app.post("/token")
        async def login(form_data: OAuth2PasswordRequestForm = Depends()):
            """Endpoint für die Anmeldung und Token-Erstellung."""
            # Prüfe die Anmeldeinformationen
            result = auth_manager.login(
                form_data.username, 
                form_data.password,
                totp_code=form_data.client_secret
            )
            
            if not result.get("success"):
                # Wenn 2FA erforderlich ist, gib eine spezielle Antwort zurück
                if result.get("require_2fa"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="2FA erforderlich",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Falscher Benutzername oder Passwort",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Erstelle eine Antwort mit dem Token
            return {
                "access_token": result["access_token"],
                "token_type": result["token_type"],
                "username": result["username"],
                "is_admin": result["is_admin"],
                "refresh_token": result.get("refresh_token")
            }
        
        @app.post("/token/refresh")
        async def refresh_token(refresh_token: str):
            """Endpoint zum Verlängern eines Tokens."""
            result = auth_manager.refresh_token(refresh_token)
            if "error" in result:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result["error"],
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return result
    
    @app.get("/models")
    async def list_models(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Listet alle verfügbaren Modelle auf."""
        return {
            "models": model_manager.list_models(),
            "count": len(model_manager.list_models())
        }
    
    @app.get("/models/{model_name}")
    async def get_model(model_name: str, current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Gibt Informationen zu einem bestimmten Modell zurück."""
        model = model_manager.get_model(model_name)
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Modell '{model_name}' nicht gefunden"
            )
        return {
            "name": model_name,
            "status": "loaded" if model else "not_loaded",
            "description": model.description if model else "",
            "size": model.size if model else 0
        }
    
    @app.post("/query")
    async def query_model(
        prompt: str,
        model: Optional[str] = None,
        current_user: dict = Depends(get_current_user) if auth_manager else None
    ):
        """Fragt ein Modell mit einem Prompt ab."""
        try:
            # Wenn kein Modell angegeben wurde, verwende das erste verfügbare Modell
            if not model:
                models = model_manager.list_models()
                if not models:
                    raise HTTPException(
                        status_code=400,
                        detail="Keine Modelle verfügbar"
                    )
                model = models[0]
            
            # Frage das Modell ab
            response = ai_engine.model_orchestrator.query(
                prompt,
                models=[model]
            )
            
            if model not in response or not response[model]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Fehler bei der Abfrage des Modells '{model}'"
                )
            
            return {
                "model": model,
                "prompt": prompt,
                "response": response[model],
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Fehler bei der Modellabfrage: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Interner Serverfehler: {str(e)}"
            )
    
    @app.get("/plugins")
    async def list_plugins(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Listet alle geladenen Plugins auf."""
        return {
            "plugins": plugin_manager.list_plugins(),
            "count": len(plugin_manager.list_plugins())
        }
    
    @app.get("/status")
    async def get_status(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Gibt den aktuellen Status des Systems zurück."""
        return {
            "status": "running",
            "ai_engine": "active" if ai_engine.running else "inactive",
            "model_manager": len(model_manager.list_models()),
            "plugins": len(plugin_manager.list_plugins()),
            "timestamp": time.time(),
            "auth_enabled": auth_manager is not None
        }
    
    @app.get("/autonomy/status")
    async def get_autonomy_status(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Gibt den Status des autonomen Lernzyklus zurück."""
        if hasattr(ai_engine, 'autonomous_loop') and ai_engine.autonomous_loop:
            return ai_engine.autonomous_loop.get_status()
        else:
            return {
                "active": False,
                "status": "not_initialized",
                "message": "Autonomer Lernzyklus ist nicht initialisiert"
            }
    
    @app.post("/autonomy/start")
    async def start_autonomy(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Startet den autonomen Lernzyklus."""
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Administratoren können den autonomen Lernzyklus starten"
            )
            
        if hasattr(ai_engine, 'autonomous_loop') and ai_engine.autonomous_loop:
            ai_engine.autonomous_loop.start()
            return {"status": "success", "message": "Autonomer Lernzyklus gestartet"}
        else:
            return {"status": "error", "message": "Autonomer Lernzyklus ist nicht initialisiert"}
    
    @app.post("/autonomy/stop")
    async def stop_autonomy(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Stoppt den autonomen Lernzyklus."""
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Administratoren können den autonomen Lernzyklus stoppen"
            )
            
        if hasattr(ai_engine, 'autonomous_loop') and ai_engine.autonomous_loop:
            ai_engine.autonomous_loop.stop()
            return {"status": "success", "message": "Autonomer Lernzyklus gestoppt"}
        else:
            return {"status": "error", "message": "Autonomer Lernzyklus ist nicht initialisiert"}
    
    @app.get("/knowledge")
    async def get_knowledge(
        category: Optional[str] = None,
        limit: int = 10,
        current_user: dict = Depends(get_current_user) if auth_manager else None
    ):
        """Gibt Wissen aus der Wissensdatenbank zurück."""
        if category:
            results = ai_engine.knowledge_base.query(category)
        else:
            results = []
            for cat in ai_engine.knowledge_base.list_categories():
                results.extend(ai_engine.knowledge_base.query(cat))
        
        return {
            "knowledge": results[:limit],
            "count": len(results),
            "limit": limit
        }
    
    @app.post("/knowledge")
    async def add_knowledge(
        category: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        current_user: dict = Depends(get_current_user) if auth_manager else None
    ):
        """Fügt neues Wissen zur Wissensdatenbank hinzu."""
        if not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Administratoren können Wissen hinzufügen"
            )
            
        entry_id = ai_engine.knowledge_base.store(category, data, metadata)
        if entry_id == -1:
            raise HTTPException(
                status_code=500,
                detail="Fehler beim Speichern des Wissens"
            )
        
        return {
            "status": "success",
            "entry_id": entry_id,
            "message": "Wissen erfolgreich gespeichert"
        }
    
    @app.get("/users/me")
    async def get_current_user_info(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Gibt Informationen über den aktuellen Benutzer zurück."""
        if not auth_manager:
            return {
                "username": "admin",
                "is_admin": True,
                "2fa_enabled": False
            }
            
        user = ai_engine.user_manager.get_user(current_user["username"])
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Benutzer nicht gefunden"
            )
            
        return {
            "username": user["username"],
            "is_admin": user["is_admin"],
            "2fa_enabled": bool(user["totp_secret"]),
            "created_at": user["created_at"],
            "last_login": user["last_login"]
        }
    
    @app.post("/2fa/setup")
    async def setup_2fa(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Richtet 2FA für den aktuellen Benutzer ein."""
        if not auth_manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="2FA ist nicht aktiviert"
            )
            
        result = auth_manager.setup_2fa(current_user["username"])
        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail=result["error"]
            )
            
        return {
            "secret": result["secret"],
            "qr_code": result["qr_code"],
            "backup_codes": result["backup_codes"]
        }
    
    @app.post("/2fa/disable")
    async def disable_2fa(current_user: dict = Depends(get_current_user) if auth_manager else None):
        """Deaktiviert 2FA für den aktuellen Benutzer."""
        if not auth_manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="2FA ist nicht aktiviert"
            )
            
        if not auth_manager.disable_2fa(current_user["username"]):
            raise HTTPException(
                status_code=500,
                detail="Fehler bei der Deaktivierung von 2FA"
            )
            
        return {"status": "success", "message": "2FA deaktiviert"}
    
    return app