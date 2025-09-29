# src/core/ai_engine.py
"""
ai_engine.py - Zentrale KI-Logik für Mindestentinel

Diese Datei implementiert die zentrale KI-Logik für das System.
Es koordiniert alle Komponenten und verwaltet den autonomen Lernzyklus.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("mindestentinel.ai_engine")

class AIBrain:
    """
    Die zentrale KI-Logik für das System.
    
    Koordiniert alle Komponenten und verwaltet den autonomen Lernzyklus.
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialisiert das AIBrain.
        
        Args:
            rules_path: Pfad zur Regelkonfiguration
        """
        self.start_time = time.time()
        self.active = False
        self.rules_path = rules_path
        self.knowledge_base = None
        self.model_manager = None
        self.model_orchestrator = None
        self.rule_engine = None
        self.protection_module = None
        self.system_monitor = None
        self.user_manager = None
        logger.info("AIBrain initialisiert.")
    
    def inject_model_manager(self, model_manager):
        """Injiziert den ModelManager."""
        self.model_manager = model_manager
        logger.debug("ModelManager injiziert.")
    
    def start(self):
        """Startet das AIBrain."""
        self.active = True
        logger.info("AIBrain gestartet.")
    
    def stop(self):
        """Stoppt das AIBrain."""
        self.active = False
        logger.info("AIBrain gestoppt.")
    
    def query(self, prompt: str, models: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Verarbeitet eine Anfrage an das KI-System.
        
        Args:
            prompt: Der Prompt
            models: Optionale Liste der Modelle
            
        Returns:
            Dict[str, Any]: Die Antworten der Modelle
        """
        if not self.active:
            logger.warning("AIBrain ist nicht aktiv. Kann keine Anfrage verarbeiten.")
            return {}
        
        if not self.model_orchestrator:
            logger.error("ModelOrchestrator nicht initialisiert. Kann keine Anfrage verarbeiten.")
            return {}
        
        # Frage die Modelle
        responses = self.model_orchestrator.query(prompt, models=models)
        
        # Speichere das Wissen
        if self.knowledge_base:
            try:
                self.knowledge_base.store("query", {
                    "prompt": prompt,
                    "models": models,
                    "responses": responses,
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Fehler beim Speichern der Anfrage: {str(e)}", exc_info=True)
        
        return responses
    
    def learn_from_experience(self, goal_id: str, examples: List[Dict[str, Any]]):
        """
        Lernt aus Erfahrungen.
        
        Args:
            goal_id: Die ID des Lernziels
            examples: Die Wissensbeispiele
        """
        if not self.active:
            logger.warning("AIBrain ist nicht aktiv. Kann nicht lernen.")
            return
        
        if not self.model_manager or not self.model_orchestrator:
            logger.error("ModelManager oder ModelOrchestrator nicht initialisiert. Kann nicht lernen.")
            return
        
        # Hier würde der eigentliche Lernprozess stattfinden
        # Für diese vereinfachte Version geben wir nur eine Logmeldung aus
        logger.info(f"Lerne aus {len(examples)} Beispielen für Ziel {goal_id}...")
        
        # In einer echten Implementierung würden Sie hier:
        # 1. Knowledge Distillation durchführen
        # 2. Ein neues Modell trainieren
        # 3. Das neue Modell registrieren
        
        # Für das Beispiel geben wir nur eine Erfolgsmeldung aus
        logger.info(f"Lernprozess für Ziel {goal_id} abgeschlossen.")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Gibt den Systemstatus zurück.
        
        Returns:
            Dict[str, Any]: Der Systemstatus
        """
        return {
            "active": self.active,
            "uptime": time.time() - self.start_time,
            "components": {
                "knowledge_base": self.knowledge_base is not None,
                "model_manager": self.model_manager is not None,
                "model_orchestrator": self.model_orchestrator is not None,
                "rule_engine": self.rule_engine is not None,
                "protection_module": self.protection_module is not None,
                "system_monitor": self.system_monitor is not None,
                "user_manager": self.user_manager is not None
            },
            "timestamp": time.time()
        }
    
    def get_knowledge(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Gibt Wissen aus der Wissensdatenbank zurück.
        
        Args:
            category: Die Kategorie
            limit: Die maximale Anzahl der Ergebnisse
            
        Returns:
            List[Dict[str, Any]]: Das Wissen
        """
        if not self.knowledge_base:
            logger.error("Wissensdatenbank nicht initialisiert.")
            return []
        
        # Hole das Wissen
        return self.knowledge_base.select(
            "SELECT * FROM knowledge WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
            (category, limit),
            decrypt_column=2  # encrypted_data ist Spalte 2
        )
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        Gibt Systemstatistiken zurück.
        
        Returns:
            Dict[str, Any]: Die Systemstatistiken
        """
        stats = {
            "uptime": time.time() - self.start_time,
            "knowledge_entries": 0,
            "model_count": 0,
            "user_count": 0,
            "active_components": 0
        }
        
        # Zähle die aktiven Komponenten
        active_components = 0
        if self.knowledge_base:
            active_components += 1
            stats["knowledge_entries"] = self.knowledge_base.get_statistics()["total_entries"]
        if self.model_manager:
            active_components += 1
            stats["model_count"] = len(self.model_manager.list_models())
        if self.user_manager:
            active_components += 1
            stats["user_count"] = len(self.user_manager.list_users())
        
        stats["active_components"] = active_components
        return stats