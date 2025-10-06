# src/core/ai_engine.py
"""
ai_engine.py - AIBrain für Mindestentinel

Diese Datei implementiert das AIBrain, das die zentrale KI-Logik enthält.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.core.knowledge_base import KnowledgeBase
from src.core.model_manager import ModelManager
from src.core.rule_engine import RuleEngine
from src.core.protection_module import ProtectionModule
from src.core.system_monitor import SystemMonitor
from src.core.multi_model_orchestrator import MultiModelOrchestrator
from src.core.knowledge_transfer import KnowledgeTransfer
from src.core.model_trainer import ModelTrainer
from src.core.autonomous_loop import AutonomousLoop

logger = logging.getLogger("mindestentinel.ai_engine")

class AIBrain:
    """Das AIBrain - zentrale KI-Logik für Mindestentinel"""
    
    def __init__(self, rules_path: Optional[str] = None):
        """Initialisiert das AIBrain
        
        Args:
            rules_path: Pfad zur Regelkonfigurationsdatei (wird ignoriert, da RuleEngine bereits initialisiert)
        """
        logger.info("AIBrain initialisiert.")
        
        # Hinweis: rules_path wird hier ignoriert, da die RuleEngine bereits in main.py initialisiert wird
        if rules_path:
            logger.warning("rules_path Parameter wird ignoriert - RuleEngine wird bereits separat initialisiert")
        
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
    
    def inject_model_manager(self, model_manager: ModelManager):
        """Injiziert den ModelManager"""
        self.model_manager = model_manager
        logger.info("ModelManager injiziert.")
    
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
            # Hole aktive Modelle - KORREKTUR: get_student_models() statt get_active_models()
            models = self.model_orchestrator.get_student_models()
            
            # Frage jedes Modell
            responses = {}
            for model_name in models:
                try:
                    # Verwende die korrekte Query-Methode
                    response = self.model_orchestrator.query(
                        model_name,
                        prompt,
                        max_tokens=max_tokens
                    )
                    responses[model_name] = response
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
                "active_models": self.model_orchestrator.get_student_models() if self.model_orchestrator else [],
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