# src/api/rest_api.py
"""
rest_api.py - REST API Endpoints für Mindestentinel

Dieses Modul implementiert die REST-API für Mindestentinel mit folgenden Endpunkten:
- /status: Systemstatus abfragen
- /query: Anfragen an das KI-System stellen
- /models: Informationen zu verfügbaren Modellen
- /knowledge: Zugriff auf die Wissensdatenbank
- /shutdown: Sauberes Herunterfahren des Systems
"""

import logging
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional
from src.core.knowledge_base import KnowledgeBase
from src.core.model_manager import ModelManager
from src.modules.plugin_manager import PluginManager
from src.core.ai_engine import AIBrain
import datetime
import os
import jwt
from jwt.exceptions import InvalidTokenError
import time

logger = logging.getLogger("mindestentinel.rest_api")

# Konfiguration für JWT
SECRET_KEY = os.getenv("MIND_API_KEY", "mindestentinel_default_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Überprüft die Gültigkeit eines JWT-Tokens
    
    Args:
        credentials: Die Authorization-Credentials
        
    Returns:
        dict: Die decodierte Payload des Tokens
        
    Raises:
        HTTPException: Wenn das Token ungültig ist
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiges Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """
    Erstellt ein neues JWT-Access-Token
    
    Args:
        data: Die Daten, die im Token gespeichert werden sollen
        expires_delta: Optionale Ablauffrist in Minuten
        
    Returns:
        str: Das signierte JWT-Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=expires_delta)
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_app(ai_engine: AIBrain, model_manager: ModelManager, plugin_manager: PluginManager) -> FastAPI:
    """
    Erstellt die FastAPI-Instanz für die REST-API
    
    Args:
        ai_engine: Die AIBrain-Instanz
        model_manager: Der ModelManager
        plugin_manager: Der PluginManager
        
    Returns:
        FastAPI: Die konfigurierte FastAPI-Instanz
    """
    app = FastAPI(
        title="Mindestentinel REST API",
        description="API für das autonome KI-System Mindestentinel",
        version="1.0.0"
    )
    
    # Root-Endpunkt
    @app.get("/")
    async def root():
        """Grundlegender Endpunkt für Systeminformationen"""
        return {
            "status": "running",
            "version": "build0015.1A",
            "autonomy_active": ai_engine.autonomous_loop.active if hasattr(ai_engine, 'autonomous_loop') and ai_engine.autonomous_loop else False,
            "model_count": len(model_manager.list_models()),
            "knowledge_entries": ai_engine.knowledge_base.get_statistics()["total_entries"] if hasattr(ai_engine, 'knowledge_base') else 0,
            "message": "Willkommen bei Mindestentinel - dem autonomen KI-System",
            "endpoints": {
                "status": "/status",
                "query": "/query",
                "models": "/models",
                "knowledge": "/knowledge",
                "shutdown": "/shutdown"
            }
        }
    
    # Status-Endpunkt
    @app.get("/status")
    async def status():
        """Gibt den aktuellen Systemstatus zurück"""
        return {
            "status": "running",
            "uptime": time.time() - ai_engine.start_time if hasattr(ai_engine, 'start_time') else 0,
            "autonomy_active": ai_engine.autonomous_loop.active if hasattr(ai_engine, 'autonomous_loop') and ai_engine.autonomous_loop else False,
            "models_loaded": model_manager.list_models(),
            "system_monitor": ai_engine.system_monitor.snapshot() if hasattr(ai_engine, 'system_monitor') else {}
        }
    
    # Query-Endpunkt
    @app.post("/query")
    async def query(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Verarbeitet eine Anfrage an das KI-System"""
        # Token überprüfen
        verify_token(credentials)
        
        # Anfrage-Body parsen
        body = await request.json()
        prompt = body.get("prompt")
        models = body.get("models", [])
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt ist erforderlich")
        
        try:
            # Abfrage an das KI-System
            responses = ai_engine.query(prompt, models=models)
            
            return {
                "prompt": prompt,
                "responses": responses,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Fehler bei der Verarbeitung der Anfrage")
    
    # Models-Endpunkt
    @app.get("/models")
    async def list_models():
        """Listet alle verfügbaren Modelle auf"""
        return {
            "models": model_manager.list_models(),
            "details": [
                {
                    "name": name,
                    "status": model_manager.get_model_status(name),
                    "config": model_manager.get_model_config(name),
                    "metadata": model_manager.get_model_metadata(name)
                }
                for name in model_manager.list_models()
            ]
        }
    
    # Knowledge-Endpunkt
    @app.get("/knowledge")
    async def get_knowledge(
        category: Optional[str] = None,
        limit: int = 100,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Gibt Wissenseinträge zurück"""
        # Token überprüfen
        verify_token(credentials)
        
        # Wissensdatenbank abfragen
        kb = ai_engine.knowledge_base
        if category:
            entries = kb.query(
                "SELECT * FROM knowledge WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                (category, limit)
            )
        else:
            entries = kb.query(
                "SELECT * FROM knowledge ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        
        return {
            "entries": entries,
            "count": len(entries),
            "limit": limit
        }
    
    # Shutdown-Endpunkt
    @app.post("/shutdown")
    async def shutdown(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Initiiert einen sauberen Shutdown des Systems"""
        # Token überprüfen
        payload = verify_token(credentials)
        
        # Prüfe, ob der Benutzer Admin-Rechte hat
        if not payload.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Nur Administratoren dürfen das System herunterfahren"
            )
        
        logger.info("Shutdown-Anfrage erhalten. Beende System...")
        
        # Starte Shutdown in einem Hintergrundthread
        def shutdown_server():
            time.sleep(1)  # Kleine Pause, damit die Antwort gesendet werden kann
            os._exit(0)  # Beende den Prozess
        
        # Starte den Shutdown-Thread
        shutdown_thread = threading.Thread(target=shutdown_server)
        shutdown_thread.daemon = True
        shutdown_thread.start()
        
        return {"status": "shutdown", "message": "Shutdown initiated"}
    
    # Login-Endpunkt
    @app.post("/login")
    async def login(request: Request):
        """Authentifiziert einen Benutzer und gibt ein JWT-Token zurück"""
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
        
        # Hier würde die eigentliche Authentifizierung stattfinden
        # In dieser Demo-Version akzeptieren wir jedes Passwort
        if not username:
            raise HTTPException(status_code=400, detail="Benutzername ist erforderlich")
        
        # Erstelle ein Token
        access_token = create_access_token(
            data={"sub": username, "is_admin": username == "admin"}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    return app