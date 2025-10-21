"""
self_learning.py
Implementiert das selbstlernende System des Mindestentinel-Frameworks.
Ermöglicht kontinuierliches Lernen und Anpassung basierend auf Erfahrungen.
"""

import logging
import os
import time
import json
from typing import Dict, Any, List, Optional, Callable, Tuple
from pathlib import Path

logger = logging.getLogger("mindestentinel.self_learning")

class SelfLearningEngine:
    """
    Hauptklasse für das selbstlernende System des Mindestentinel-Frameworks.
    Ermöglicht kontinuierliches Lernen und Anpassung basierend auf Erfahrungen.
    """
    
    def __init__(
        self,
        rule_engine: Optional['RuleEngine'] = None,
        model_manager: Optional['ModelManager'] = None,
        config: Optional[Dict[str, Any]] = None,
        knowledge_base_path: str = "data/knowledge/self_learning.json"
    ):
        """
        Initialisiert die SelfLearningEngine.
        
        Args:
            rule_engine: Optional bereitgestellte RuleEngine-Instanz
            model_manager: Optional bereitgestellter ModelManager
            config: Optionale Konfigurationsparameter
            knowledge_base_path: Pfad zur Wissensdatenbank
        """
        logger.info("Initialisiere SelfLearningEngine...")
        self.config = config or {}
        self.rule_engine = rule_engine
        self.model_manager = model_manager
        self.knowledge_base_path = knowledge_base_path
        self.learning_active = True
        self.learning_rate = self.config.get('learning_rate', 0.1)
        self.memory_size = self.config.get('memory_size', 1000)
        
        # Lade oder erstelle Wissensdatenbank
        self.knowledge_base = self._load_knowledge_base()
        
        # Initialisiere Lernhistorie
        self.learning_history = []
        
        logger.info("SelfLearningEngine erfolgreich initialisiert")
    
    def start(self) -> None:
        """Startet die SelfLearningEngine"""
        logger.info("Starte SelfLearningEngine...")
        self.learning_active = True
        logger.info("SelfLearningEngine gestartet")
    
    def stop(self) -> None:
        """Stoppt die SelfLearningEngine"""
        logger.info("Stoppe SelfLearningEngine...")
        self.learning_active = False
        logger.info("SelfLearningEngine gestoppt")
    
    def is_active(self) -> bool:
        """Gibt an, ob die SelfLearningEngine aktiv ist"""
        return self.learning_active
    
    def process_experience(
        self,
        experience: Dict[str, Any],
        reward: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verarbeitet eine Erfahrung und passt das Wissen an.
        
        Args:
            experience: Die zu verarbeitende Erfahrung
            reward: Die Belohnung für die Erfahrung
            context: Optionaler Kontext für die Verarbeitung
            
        Returns:
            Dict[str, Any]: Ergebnis der Verarbeitung
        """
        if not self.learning_active:
            logger.debug("SelfLearningEngine ist deaktiviert, überspringe Verarbeitung")
            return {
                "status": "skipped",
                "message": "SelfLearningEngine ist deaktiviert"
            }
        
        logger.debug(f"Verarbeite Erfahrung mit Belohnung {reward}: {experience}")
        
        try:
            # Speichere Erfahrung in der Lernhistorie
            self._store_experience(experience, reward, context)
            
            # Aktualisiere das Wissen basierend auf der Erfahrung
            learning_result = self._update_knowledge(experience, reward, context)
            
            # Speichere die aktualisierte Wissensdatenbank
            self._save_knowledge_base()
            
            logger.debug("Erfahrung erfolgreich verarbeitet")
            return {
                "status": "success",
                "result": learning_result
            }
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung der Erfahrung: {str(e)}")
            return {
                "status": "error",
                "code": 500,
                "message": f"Interner Fehler: {str(e)}"
            }
    
    def _store_experience(
        self,
        experience: Dict[str, Any],
        reward: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Speichert eine Erfahrung in der Lernhistorie"""
        timestamp = time.time()
        self.learning_history.append({
            "timestamp": timestamp,
            "experience": experience,
            "reward": reward,
            "context": context
        })
        
        # Begrenze die Größe der Lernhistorie
        if len(self.learning_history) > self.memory_size:
            self.learning_history = self.learning_history[-self.memory_size:]
    
    def _update_knowledge(
        self,
        experience: Dict[str, Any],
        reward: float,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Aktualisiert das Wissen basierend auf einer Erfahrung"""
        result = {
            "knowledge_updates": 0,
            "updated_categories": []
        }
        
        # Extrahiere relevante Informationen aus der Erfahrung
        category = experience.get("category", "general")
        action = experience.get("action", "unknown")
        outcome = experience.get("outcome", {})
        
        # Erstelle oder aktualisiere den Kategorie-Eintrag
        if category not in self.knowledge_base["categories"]:
            self.knowledge_base["categories"][category] = {
                "total_experiences": 0,
                "total_reward": 0,
                "actions": {}
            }
        
        category_data = self.knowledge_base["categories"][category]
        category_data["total_experiences"] += 1
        category_data["total_reward"] += reward
        
        # Erstelle oder aktualisiere den Aktions-Eintrag
        if action not in category_data["actions"]:
            category_data["actions"][action] = {
                "count": 0,
                "total_reward": 0,
                "last_outcome": None,
                "parameters": {}
            }
        
        action_data = category_data["actions"][action]
        action_data["count"] += 1
        action_data["total_reward"] += reward
        action_data["last_outcome"] = outcome
        
        # Aktualisiere Parameter, falls vorhanden
        if "parameters" in experience:
            for param, value in experience["parameters"].items():
                if param not in action_data["parameters"]:
                    action_data["parameters"][param] = {
                        "values": [],
                        "average": value
                    }
                
                param_data = action_data["parameters"][param]
                param_data["values"].append(value)
                
                # Begrenze die Anzahl der gespeicherten Werte
                if len(param_data["values"]) > 100:
                    param_data["values"] = param_data["values"][-100:]
                
                # Berechne neuen Durchschnitt
                param_data["average"] = sum(param_data["values"]) / len(param_data["values"])
        
        # Berechne die aktuelle Belohnungsrate für diese Aktion
        action_data["reward_rate"] = action_data["total_reward"] / action_data["count"]
        
        # Markiere Update
        result["knowledge_updates"] += 1
        if category not in result["updated_categories"]:
            result["updated_categories"].append(category)
        
        return result
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Lädt die Wissensdatenbank aus einer Datei"""
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
            
            # Prüfe, ob die Datei existiert
            if os.path.exists(self.knowledge_base_path):
                with open(self.knowledge_base_path, 'r') as f:
                    knowledge_base = json.load(f)
                logger.debug(f"Wissensdatenbank geladen: {self.knowledge_base_path}")
                return knowledge_base
            else:
                # Erstelle eine neue Wissensdatenbank
                knowledge_base = {
                    "version": "1.0",
                    "created_at": time.time(),
                    "categories": {}
                }
                self._save_knowledge_base(knowledge_base)
                logger.info(f"Neue Wissensdatenbank erstellt: {self.knowledge_base_path}")
                return knowledge_base
        except Exception as e:
            logger.error(f"Fehler beim Laden der Wissensdatenbank: {str(e)}")
            # Erstelle eine neue Wissensdatenbank im Fehlerfall
            return {
                "version": "1.0",
                "created_at": time.time(),
                "categories": {}
            }
    
    def _save_knowledge_base(self, knowledge_base: Optional[Dict[str, Any]] = None) -> None:
        """Speichert die Wissensdatenbank in einer Datei"""
        try:
            # Verwende die aktuelle Wissensdatenbank, wenn keine übergeben wurde
            if knowledge_base is None:
                knowledge_base = self.knowledge_base
            
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
            
            # Speichere die Wissensdatenbank
            with open(self.knowledge_base_path, 'w') as f:
                json.dump(knowledge_base, f, indent=2)
            
            logger.debug(f"Wissensdatenbank gespeichert: {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Wissensdatenbank: {str(e)}")
    
    def get_knowledge_base(self) -> Dict[str, Any]:
        """Gibt die aktuelle Wissensdatenbank zurück"""
        return self.knowledge_base
    
    def get_learning_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Gibt die Lernhistorie zurück (begrenzt auf die letzten Einträge)"""
        return self.learning_history[-limit:]
    
    def get_best_action(self, category: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Gibt die beste Aktion für eine Kategorie basierend auf dem Wissen zurück.
        
        Args:
            category: Die Kategorie, für die die beste Aktion gesucht wird
            context: Optionaler Kontext für die Entscheidung
            
        Returns:
            Dict[str, Any]: Die beste Aktion mit Metadaten
        """
        logger.debug(f"Suche beste Aktion für Kategorie: {category}")
        
        # Prüfe, ob die Kategorie existiert
        if category not in self.knowledge_base["categories"]:
            logger.warning(f"Kategorie nicht gefunden: {category}")
            return {
                "action": "default",
                "confidence": 0.0,
                "reason": "Kategorie nicht gefunden"
            }
        
        category_data = self.knowledge_base["categories"][category]
        
        # Prüfe, ob es Aktionen für die Kategorie gibt
        if not category_data["actions"]:
            logger.warning(f"Keine Aktionen für Kategorie gefunden: {category}")
            return {
                "action": "default",
                "confidence": 0.0,
                "reason": "Keine Aktionen vorhanden"
            }
        
        # Finde die Aktion mit der höchsten Belohnungsrate
        best_action = None
        best_reward_rate = float('-inf')
        
        for action, action_data in category_data["actions"].items():
            reward_rate = action_data.get("reward_rate", float('-inf'))
            if reward_rate > best_reward_rate:
                best_action = action
                best_reward_rate = reward_rate
        
        # Berechne das Vertrauen basierend auf der Anzahl der Erfahrungen
        confidence = min(1.0, category_data["total_experiences"] / 10.0)
        
        logger.debug(f"Gefundene beste Aktion: {best_action} mit Belohnungsrate {best_reward_rate} und Vertrauen {confidence}")
        
        return {
            "action": best_action,
            "reward_rate": best_reward_rate,
            "confidence": confidence,
            "total_experiences": category_data["total_experiences"]
        }
    
    def adapt_to_feedback(
        self,
        experience_id: str,
        feedback: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Passt das Wissen basierend auf Nutzerfeedback an.
        
        Args:
            experience_id: ID der Erfahrung, auf die sich das Feedback bezieht
            feedback: Das Nutzerfeedback
            context: Optionaler Kontext für die Anpassung
            
        Returns:
            Dict[str, Any]: Ergebnis der Anpassung
        """
        logger.debug(f"Verarbeite Feedback für Erfahrung {experience_id}: {feedback}")
        
        try:
            # Hier würde die Anpassung basierend auf dem Feedback stattfinden
            # In einer realen Implementierung würden die Gewichte angepasst
            # und das Wissen aktualisiert werden
            
            # Platzhalter für die konkrete Implementierung
            adjustment_factor = feedback.get("adjustment_factor", 1.0)
            new_knowledge = {}
            
            # Simuliere eine Anpassung
            for category, category_data in self.knowledge_base["categories"].items():
                for action, action_data in category_data["actions"].items():
                    # Passe die Belohnungsrate basierend auf dem Feedback an
                    if "reward_rate" in action_data:
                        action_data["reward_rate"] *= adjustment_factor
                        new_knowledge[f"{category}.{action}"] = action_data["reward_rate"]
            
            # Speichere die aktualisierte Wissensdatenbank
            self._save_knowledge_base()
            
            logger.debug("Feedback erfolgreich verarbeitet")
            return {
                "status": "success",
                "adjusted_knowledge": new_knowledge
            }
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung des Feedbacks: {str(e)}")
            return {
                "status": "error",
                "code": 500,
                "message": f"Interner Fehler: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Status der SelfLearningEngine zurück"""
        return {
            "status": "running" if self.learning_active else "stopped",
            "knowledge_base_size": len(self.knowledge_base["categories"]),
            "learning_history_size": len(self.learning_history),
            "memory_size": self.memory_size,
            "learning_rate": self.learning_rate,
            "timestamp": time.time()
        }
    
    def reset(self) -> None:
        """Setzt die SelfLearningEngine auf den Ausgangszustand zurück"""
        logger.info("Setze SelfLearningEngine zurück...")
        
        # Erstelle eine neue Wissensdatenbank
        self.knowledge_base = {
            "version": "1.0",
            "created_at": time.time(),
            "categories": {}
        }
        
        # Leere die Lernhistorie
        self.learning_history = []
        
        # Speichere die zurückgesetzte Wissensdatenbank
        self._save_knowledge_base()
        
        logger.info("SelfLearningEngine erfolgreich zurückgesetzt")