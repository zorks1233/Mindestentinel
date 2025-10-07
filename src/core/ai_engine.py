# src/core/ai_engine.py
"""
ai_engine.py - AIBrain für Mindestentinel

Diese Datei implementiert das AIBrain, das die zentrale KI-Logik enthält.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("mindestentinel.ai_engine")

class AIBrain:
    """Das AIBrain - zentrale KI-Logik für Mindestentinel"""
    
    def __init__(self):
        """Initialisiert das AIBrain"""
        logger.info("AIBrain initialisiert.")
        
        # Komponenten
        self.knowledge_base = None
        self.model_manager = None
        self.model_orchestrator = None
        self.rule_engine = None
        self.protection_module = None
        self.system_monitor = None
        self.knowledge_transfer = None
        self.model_trainer = None
        self.autonomous_loop = None
    
    def inject_model_manager(self, model_manager):
        """Injiziert den ModelManager"""
        self.model_manager = model_manager
        logger.info("ModelManager injiziert.")
    
    def inject_rule_engine(self, rule_engine):
        """Injiziert die RuleEngine"""
        self.rule_engine = rule_engine
        logger.info("RuleEngine injiziert.")
    
    def start(self):
        """Startet das AIBrain (Hintergrundprozesse etc.)"""
        logger.info("AIBrain gestartet.")
    
    def stop(self):
        """Stoppt das AIBrain"""
        logger.info("AIBrain gestoppt.")
    
    def query(self, prompt: str, max_tokens: int = 512) -> Dict[str, str]:
        """
        Verarbeitet eine Benutzeranfrage
        
        Args:
            prompt: Die Benutzeranfrage
            max_tokens: Maximale Anzahl der Tokens für die Antwort
            
        Returns:
            Dict[str, str]: Antworten von allen Modellen
        """
        logger.info(f"Verarbeite Abfrage: {prompt}")
        
        try:
            # Hole Schüler-Modelle
            models = ["mindestentinel"]
            
            # Frage jedes Modell
            responses = {}
            for model_name in models:
                try:
                    # Simuliere eine einfache Antwort
                    if "Hauptstadt" in prompt and "Frankreich" in prompt:
                        responses[model_name] = "Die Hauptstadt von Frankreich ist Paris."
                    else:
                        responses[model_name] = f"Simulierte Antwort auf '{prompt[:30]}...'"
                except Exception as e:
                    logger.error(f"Fehler bei der Abfrage von {model_name}: {str(e)}", exc_info=True)
                    responses[model_name] = "Entschuldigung, ich konnte diese Anfrage nicht verarbeiten."
            
            return responses
        except Exception as e:
            logger.error(f"Kritischer Fehler bei der Abfrage: {str(e)}", exc_info=True)
            raise
    
    def learn_from_interaction(self, prompt: str, response: str, feedback: Optional[Dict] = None):
        """
        Lernt aus einer Benutzerinteraktion
        
        Args:
            prompt: Die Benutzeranfrage
            response: Die Systemantwort
            feedback: Optionales Feedback des Benutzers
        """
        try:
            # Speichere die Interaktion im Wissensspeicher
            if self.knowledge_base:
                self.knowledge_base.add_knowledge(
                    context="user_interaction",
                    content=f"Prompt: {prompt}\nResponse: {response}",
                    source="user_interaction",
                    confidence=feedback.get("confidence", 0.8) if feedback else 0.8
                )
            
            logger.info("Gelernt aus Benutzerinteraktion")
        except Exception as e:
            logger.error(f"Fehler beim Lernen aus Interaktion: {str(e)}", exc_info=True)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Systemstatus zurück"""
        try:
            status = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "running",
                "model_count": len(self.model_manager.list_models()) if self.model_manager else 0,
                "active_models": ["mindestentinel"],
                "knowledge_entries": len(self.knowledge_base.get_knowledge()) if self.knowledge_base else 0,
                "system_health": self.system_monitor.get_health_status() if self.system_monitor else "unknown"
            }
            return status
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Systemstatus: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }