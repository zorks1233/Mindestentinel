# src/api/rest_api.py
"""
rest_api.py - REST API Endpoints für Mindestentinel

Dieses Modul implementiert die REST-API für Mindestentinel mit folgenden Endpunkten:
- /status: Systemstatus abfragen
- /query: Anfragen an das KI-System stellen
- /models: Informationen zu verfügbaren Modellen
- /knowledge: Zugriff auf die Wissensdatenbank
- /auth/login: Authentifizierung für Token-Erstellung
- /admin: Admin-Endpunkte (nur mit Admin-Token zugänglich)
- /shutdown: Sauberes Herunterfahren des Systems
"""

import logging
from fastapi import FastAPI, HTTPException, Depends, Request, status as fastapi_status
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
import threading
from passlib.context import CryptContext

logger = logging.getLogger("mindestentinel.rest_api")

# Konfiguration für JWT
SECRET_KEY = os.getenv("MIND_API_KEY", "mindestentinel_default_secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Passwort-Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
            status_code=fastapi_status.HTTP_401_UNAUTHORIZED,
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
            "version": "build0015.2A",
            "autonomy_active": ai_engine.autonomous_loop.active if hasattr(ai_engine, 'autonomous_loop') and ai_engine.autonomous_loop else False,
            "model_count": len(model_manager.list_models()),
            "knowledge_entries": ai_engine.knowledge_base.get_statistics()["total_entries"] if hasattr(ai_engine, 'knowledge_base') else 0,
            "message": "Willkommen bei Mindestentinel - dem autonomen KI-System",
            "endpoints": {
                "status": "/status",
                "query": "/query",
                "models": "/models",
                "knowledge": "/knowledge",
                "auth": "/auth/login",
                "admin": "/admin",
                "shutdown": "/shutdown"
            }
        }
    
    # Status-Endpunkt
    @app.get("/status")
    async def system_status():
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
            raise HTTPException(status_code=fastapi_status.HTTP_400_BAD_REQUEST, detail="Prompt ist erforderlich")
        
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
            raise HTTPException(status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fehler bei der Verarbeitung der Anfrage")
    
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
            entries = kb.select(
                "SELECT * FROM knowledge WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                (category, limit),
                decrypt_column=2  # encrypted_data ist Spalte 2 (0-basiert)
            )
        else:
            entries = kb.select(
                "SELECT * FROM knowledge ORDER BY timestamp DESC LIMIT ?",
                (limit,),
                decrypt_column=2  # encrypted_data ist Spalte 2 (0-basiert)
            )
        
        return {
            "entries": entries,
            "count": len(entries),
            "limit": limit
        }
    
    # Auth-Endpunkt
    @app.post("/auth/login")
    async def login(request: Request):
        """Authentifiziert einen Benutzer und gibt ein JWT-Token zurück"""
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
        
        # Überprüfe, ob Benutzername und Passwort vorhanden sind
        if not username or not password:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail="Benutzername und Passwort sind erforderlich"
            )
        
        # Authentifiziere gegen die Datenbank
        try:
            user = authenticate_user(username, password)
            if not user:
                raise HTTPException(
                    status_code=fastapi_status.HTTP_401_UNAUTHORIZED,
                    detail="Ungültiger Benutzername oder Passwort",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Erstelle ein Token
            access_token = create_access_token(
                data={"sub": username, "is_admin": bool(user["is_admin"])}
            )
            
            return {
                "token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "is_admin": bool(user["is_admin"])
            }
        except Exception as e:
            logger.error(f"Fehler bei der Authentifizierung: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Interner Serverfehler bei der Authentifizierung"
            )
    
    def authenticate_user(username: str, password: str) -> Optional[Dict]:
        """
        Authentifiziert einen Benutzer gegen die Datenbank.
        
        Args:
            username: Der Benutzername
            password: Das Passwort
            
        Returns:
            Optional[Dict]: Benutzerdaten, falls erfolgreich, sonst None
        """
        # Hole Benutzer aus der Datenbank (KEINE Entschlüsselung nötig)
        kb = ai_engine.knowledge_base
        users = kb.select(
            "SELECT id, username, password_hash, is_admin, created_at FROM users WHERE username = ?",
            (username,),
            decrypt_column=None  # Keine Entschlüsselung für Benutzertabelle
        )
        
        if not users:
            logger.warning(f"Benutzer '{username}' nicht gefunden")
            return None
            
        user = users[0]
        
        # Überprüfe das Passwort
        if not pwd_context.verify(password, user["password_hash"]):
            logger.warning(f"Falsches Passwort für Benutzer '{username}'")
            return None
        
        # Aktualisiere letzte Anmeldezeit
        kb.query(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.datetime.now().isoformat(), user["id"])
        )
        
        return {
            "id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"],
            "created_at": user["created_at"]
        }
    
    # Admin-Endpunkte (nur für Admins)
    @app.get("/admin/users")
    async def list_users(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Listet alle Benutzer auf (nur für Admins)"""
        payload = verify_token(credentials)
        
        # KORRIGIERTE PRÜFUNG: Überprüfe explizit, ob is_admin True ist
        is_admin = payload.get("is_admin", False)
        if not (is_admin is True or is_admin == 1):
            raise HTTPException(
                status_code=fastapi_status.HTTP_403_FORBIDDEN,
                detail="Nur Administratoren dürfen Benutzer auflisten"
            )
        
        # Hole Benutzer aus der Datenbank (KEINE Entschlüsselung nötig)
        kb = ai_engine.knowledge_base
        users = kb.select(
            "SELECT id, username, is_admin, created_at, last_login FROM users ORDER BY created_at DESC",
            decrypt_column=None  # Keine Entschlüsselung für Benutzertabelle
        )
        
        return {
            "users": [
                {
                    "id": user["id"],
                    "username": user["username"],
                    "is_admin": bool(user["is_admin"]),
                    "created_at": user["created_at"],
                    "last_login": user["last_login"]
                }
                for user in users
            ]
        }
    
    # Shutdown-Endpunkt
    @app.post("/shutdown")
    async def shutdown(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Initiiert einen sauberen Shutdown des Systems"""
        # Token überprüfen
        payload = verify_token(credentials)
        
        # KORRIGIERTE PRÜFUNG: Überprüfe explizit, ob is_admin True ist
        is_admin = payload.get("is_admin", False)
        if not (is_admin is True or is_admin == 1):
            raise HTTPException(
                status_code=fastapi_status.HTTP_403_FORBIDDEN,
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
    
    return app