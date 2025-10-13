# src/api/rest_api.py
"""
rest_api.py - REST API Endpunkte für Mindestentinel

Diese Datei definiert die REST API Endpunkte für das System.
"""

import os
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional

from core.ai_engine import AIBrain
from core.model_manager import ModelManager
from modules.plugin_manager import PluginManager
from core.rule_engine import RuleEngine
from core.user_manager import UserManager
from core.auth_manager import AuthManager

logger = logging.getLogger("mindestentinel.api.rest")


def create_app(
    brain: AIBrain,
    model_manager: ModelManager,
    plugin_manager: Optional[PluginManager] = None,
    rule_engine: Optional[RuleEngine] = None,
    user_manager: Optional[UserManager] = None,
    auth_manager: Optional[AuthManager] = None
) -> FastAPI:
    """
    Erstellt und konfiguriert die FastAPI-App.

    Args:
        brain: Die AIBrain-Instanz
        model_manager: Der ModelManager
        plugin_manager: Der PluginManager (optional)
        rule_engine: Der RuleEngine (optional)
        user_manager: Der UserManager (optional)
        auth_manager: Der AuthManager (optional)

    Returns:
        Die konfigurierte FastAPI-Instanz
    """
    logger.info("Erstelle REST API...")

    # Sicherstellen, dass ein AuthManager vorhanden ist
    if auth_manager is None:
        logger.warning("Kein AuthManager übergeben - verwende Dummy-Authentifizierung")
        # Erstelle einen temporären AuthManager für die Initialisierung
        from core.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        user_manager = UserManager(kb) if user_manager is None else user_manager
        auth_manager = AuthManager(kb, user_manager)

    # Erstelle die FastAPI-App
    app = FastAPI(
        title="Mindestentinel API",
        description="API für die Mindestentinel AGI-Plattform",
        version="1.0.0"
    )

    # CORS konfigurieren
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gesundheitsprüfung
    @app.get("/health", include_in_schema=False)
    async def health_check():
        """Einfache Gesundheitsprüfung"""
        return {"status": "healthy"}

    # Status-Endpunkt
    @app.get("/status")
    async def get_status(current_user: dict = Depends(auth_manager.get_current_user)):
        """Gibt den aktuellen Systemstatus zurück"""
        return {
            "status": "running",
            "user": current_user["username"],
            "is_admin": current_user["is_admin"]
        }

    # Query-Endpunkt
    @app.post("/query")
    async def query(
        request: Request,
        current_user: dict = Depends(auth_manager.get_current_user)
    ):
        """Verarbeitet eine Benutzeranfrage"""
        try:
            data = await request.json()
            prompt = data.get("prompt")

            if not prompt:
                raise HTTPException(status_code=400, detail="Keine Eingabeaufforderung angegeben")

            # Überprüfe, ob der Benutzer berechtigt ist, Abfragen durchzuführen
            if not rule_engine or not rule_engine.check_rule("user_query", {"user": current_user, "prompt": prompt}):
                raise HTTPException(status_code=403, detail="Zugriff verweigert")

            # Verarbeite die Anfrage
            response = brain.process_query(prompt)

            return {"response": response}

        except Exception as e:
            logger.error(f"Fehler bei der Abfrageverarbeitung: {str(e)}")
            raise HTTPException(status_code=500, detail="Fehler bei der Verarbeitung der Anfrage")

    # Modell-Endpunkte
    @app.get("/models")
    async def list_models(current_user: dict = Depends(auth_manager.get_current_user)):
        """Listet alle verfügbaren Modelle auf"""
        return {"models": model_manager.list_models()}

    @app.post("/models/{model_name}/load")
    async def load_model(model_name: str, current_user: dict = Depends(auth_manager.get_current_user)):
        """Lädt ein spezifisches Modell"""
        if not rule_engine or not rule_engine.check_rule("load_model",
                                                         {"user": current_user, "model_name": model_name}):
            raise HTTPException(status_code=403, detail="Zugriff verweigert")

        try:
            model_manager.load_model(model_name)
            return {"status": "success", "message": f"Modell {model_name} geladen"}
        except Exception as e:
            logger.error(f"Fehler beim Laden des Modells {model_name}: {str(e)}")
            raise HTTPException(status_code=500, detail="Fehler beim Laden des Modells")

    # Plugin-Endpunkte
    if plugin_manager:
        @app.get("/plugins")
        async def list_plugins(current_user: dict = Depends(auth_manager.get_current_user)):
            """Listet alle verfügbaren Plugins auf"""
            return {"plugins": plugin_manager.list_plugins()}

        @app.post("/plugins/{plugin_name}/load")
        async def load_plugin(plugin_name: str, current_user: dict = Depends(auth_manager.get_current_user)):
            """Lädt ein spezifisches Plugin"""
            if not rule_engine or not rule_engine.check_rule("load_plugin",
                                                             {"user": current_user, "plugin_name": plugin_name}):
                raise HTTPException(status_code=403, detail="Zugriff verweigert")

            try:
                plugin_manager.load_plugin(plugin_name)
                return {"status": "success", "message": f"Plugin {plugin_name} geladen"}
            except Exception as e:
                logger.error(f"Fehler beim Laden des Plugins {plugin_name}: {str(e)}")
                raise HTTPException(status_code=500, detail="Fehler beim Laden des Plugins")

    # Admin-Endpunkte
    @app.get("/admin/users")
    async def list_users(current_user: dict = Depends(auth_manager.get_current_user)):
        """Listet alle Benutzer auf (nur für Admins)"""
        if not current_user["is_admin"]:
            raise HTTPException(status_code=403, detail="Nur für Administratoren")

        if user_manager:
            return {"users": user_manager.list_users()}
        return {"users": []}

    # Shutdown-Endpunkt
    @app.post("/shutdown")
    async def shutdown(request: Request, current_user: dict = Depends(auth_manager.get_current_user)):
        """Startet einen sauberen Shutdown des Systems"""
        if not current_user["is_admin"]:
            raise HTTPException(status_code=403, detail="Nur für Administratoren")

        logger.info(f"Shutdown-Befehl erhalten von {current_user['username']}")

        # Hier könnten wir zusätzliche Cleanup-Aktionen durchführen

        # Starte den Shutdown in einem separaten Thread, damit die Antwort gesendet werden kann
        import threading
        def shutdown_server():
            import time
            time.sleep(1)  # Kleine Verzögerung, um die Antwort zu senden
            os._exit(0)  # Beende den Prozess

        threading.Thread(target=shutdown_server).start()

        return {"status": "shutdown", "message": "System wird heruntergefahren"}

    logger.info("REST API erfolgreich initialisiert")
    return app
