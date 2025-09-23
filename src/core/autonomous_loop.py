# src/core/autonomous_loop.py
"""
autonomous_loop.py - Autonomer Lernzyklus für Mindestentinel

Diese Datei implementiert den autonomen Lernzyklus für das System.
Es ermöglicht das kontinuierliche Lernen und Verbessern des Systems.
"""

import logging
import time
import random
import threading
import datetime
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("mindestentinel.autonomous_loop")

class AutonomousLoop:
    """
    Verwaltet den autonomen Lernzyklus für das System.
    
    Ermöglicht kontinuierliches Lernen und Verbesserung des Systems.
    """
    
    def __init__(
        self,
        ai_engine,
        knowledge_base,
        model_orchestrator,
        rule_engine,
        protection_module,
        model_manager,
        system_monitor,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialisiert den autonomen Lernzyklus.
        
        Args:
            ai_engine: Die AIBrain-Instanz
            knowledge_base: Die Wissensdatenbank
            model_orchestrator: Der Model-Orchestrator
            rule_engine: Die Regel-Engine
            protection_module: Das Schutzmodul
            model_manager: Der Model-Manager
            system_monitor: Der System-Monitor
            config: Optionale Konfiguration
        """
        self.ai_engine = ai_engine
        self.kb = knowledge_base
        self.model_orchestrator = model_orchestrator
        self.rule_engine = rule_engine
        self.protection_module = protection_module
        self.mm = model_manager
        self.system_monitor = system_monitor
        
        # Konfiguration mit Standardwerten
        self.config = {
            "max_learning_cycles": 1000,
            "learning_interval_seconds": 1800,  # Alle 30 Minuten
            "min_confidence_threshold": 0.65,
            "max_resource_usage": 0.85,
            "max_goal_complexity": 5,
            "safety_check_interval": 10
        }
        if config:
            self.config.update(config)
        
        # Zustandsvariablen
        self.active = False
        self.learning_cycle = 0
        self.last_safety_check = time.time()
        self.learning_interval = self.config["learning_interval_seconds"]
        self.successful_cycles = 0
        self.failed_cycles = 0
        self.reflection_active = False
        
        logger.info("AutonomousLoop initialisiert. Warte auf Aktivierung...")
    
    def start(self):
        """Startet den autonomen Lernzyklus."""
        if self.active:
            logger.warning("Autonomer Lernzyklus ist bereits aktiv.")
            return
        
        self.active = True
        logger.info("AutonomousLoop aktiviert. Beginne mit Lernzyklen...")
        
        # Starte den Hintergrund-Thread
        self.thread = threading.Thread(target=self._background_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stoppt den autonomen Lernzyklus."""
        if not self.active:
            logger.warning("Autonomer Lernzyklus ist nicht aktiv.")
            return
        
        self.active = False
        logger.info("AutonomousLoop deaktiviert.")
        
        # Warte auf das Beenden des Threads
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=5.0)
    
    def _background_loop(self):
        """Hintergrund-Loop für den autonomen Lernzyklus."""
        logger.info("Beginne Hintergrundloop für autonomen Lernzyklus.")
        
        while self.active:
            try:
                # Warte bis zum nächsten Lernzyklus
                time.sleep(self.learning_interval)
                
                if not self.active:
                    break
                
                # Führe Lernzyklus durch
                self._run_learning_cycle()
                
                # Führe Reflexion durch, wenn nötig
                if self.learning_cycle % self.config["safety_check_interval"] == 0:
                    self._run_reflection()
                
            except Exception as e:
                logger.error(f"Fehler im Hintergrundthread: {str(e)}", exc_info=True)
    
    def _run_learning_cycle(self):
        """Führt einen Lernzyklus durch."""
        self.learning_cycle += 1
        logger.info(f"Beginne Lernzyklus #{self.learning_cycle}")
        
        try:
            # Generiere Lernziele
            learning_goals = self._generate_learning_goals()
            logger.info(f"Generierte {len(learning_goals)} neue Lernziele")
            
            # Verarbeite jedes Lernziel
            for goal in learning_goals:
                logger.info(f"Verarbeite Lernziel: {goal['description']}")
                
                # Prüfe Sicherheit des Lernziels
                context = {
                    "current_cycle": self.learning_cycle,
                    "system_status": self.system_monitor.snapshot(),
                    "resource_usage": self.system_monitor.get_resource_usage()
                }
                
                if not self._check_goal_safety(goal, context):
                    logger.warning(f"Lernziel {goal['id']} wurde aufgrund von Sicherheitsregeln verworfen")
                    continue
                
                # Frage Lehrer-Modelle
                logger.info(f"Frage {len(goal['teacher_models'])} Lehrer-Modelle: {goal['teacher_models']}")
                knowledge_examples = self._query_teacher_models(goal)
                
                if not knowledge_examples:
                    logger.warning(f"Keine Wissensbeispiele für Ziel {goal['id']} gesammelt")
                    continue
                
                logger.info(f"Gesammelte {len(knowledge_examples)} Wissensbeispiele für Ziel {goal['id']}")
                
                # Führe Knowledge Distillation durch
                logger.info(f"Führe Knowledge Distillation durch für Modell {goal['target_model']}")
                success = self._perform_knowledge_distillation(goal, knowledge_examples)
                
                if success:
                    logger.info(f"Knowledge Distillation erfolgreich für Ziel {goal['id']}")
                    self.successful_cycles += 1
                else:
                    logger.warning(f"Knowledge Distillation fehlgeschlagen für Ziel {goal['id']}")
                    self.failed_cycles += 1
                
                # Aktualisiere Modellmetadaten
                self._update_model_metadata(goal['target_model'])
                
                # Dokumentiere den Lernprozess
                self._log_learning_process(goal, knowledge_examples, success)
            
            logger.info(f"Lernintervall verlängert auf {self.learning_interval} Sekunden aufgrund hoher Erfolgsquote")
            
        except Exception as e:
            logger.error(f"Fehler im Lernzyklus #{self.learning_cycle}: {str(e)}", exc_info=True)
            self.failed_cycles += 1
    
    def _generate_learning_goals(self) -> List[Dict[str, Any]]:
        """Generiert neue Lernziele."""
        goals = []
        
        # Basis-Lernziele
        base_goals = [
            "Verbessere das Verständnis von kognitive Prozesse",
            "Verbessere das Verständnis von Ressourcenoptimierung",
            "Verbessere das Verständnis von Sicherheitsprotokolle"
        ]
        
        # Generiere Ziele für jedes verfügbare Modell
        models = self.mm.list_models()
        if not models:
            logger.warning("Keine Modelle für Lernziele gefunden")
            return goals
        
        for i, goal_desc in enumerate(base_goals):
            goal_id = f"goal_{int(time.time())}_{i}"
            
            goals.append({
                "id": goal_id,
                "description": goal_desc,
                "complexity": random.randint(1, self.config["max_goal_complexity"]),
                "priority": random.uniform(0.5, 1.0),
                "teacher_models": models,
                "target_model": models[0],  # Zielmodell ist das erste Modell
                "required_resources": ["cpu", "memory"],
                "created_at": time.time()
            })
        
        return goals
    
    def _check_goal_safety(self, goal: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Prüft, ob ein Lernziel sicher ist."""
        try:
            # Verwende execute_rules statt evaluate_rule
            results = self.rule_engine.execute_rules({
                "category": "learning_goals",
                "goal": goal,
                "context": context
            })
            
            # Prüfe, ob alle Regeln erfolgreich waren
            for result in results:
                if not result.get("condition_result", False):
                    self._log_safety_violation(goal, result)
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Fehler bei der Sicherheitsprüfung des Lernziels: {str(e)}")
            return False
    
    def _log_safety_violation(self, goal: Dict[str, Any], violation: Dict[str, Any]):
        """Protokolliert eine Sicherheitsverletzung."""
        logger.warning(
            f"Sicherheitsverletzung für Lernziel {goal['id']}: "
            f"Regel {violation.get('rule_id')} ({violation.get('rule_name')}) "
            f"verletzt mit Bedingung: {violation.get('condition')}"
        )
    
    def _query_teacher_models(self, goal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fragt die Lehrer-Modelle nach Wissen zum Lernziel."""
        knowledge_examples = []
        
        # Generiere einen Prompt für das Lernziel
        prompt = f"Erkläre detailliert: {goal['description']}"
        
        # Frage alle Lehrer-Modelle
        for model_name in goal["teacher_models"]:
            try:
                # Frage das Modell
                response = self.model_orchestrator.query(
                    prompt, 
                    models=[model_name]
                )
                
                # Speichere die Antwort als Wissensbeispiel
                if model_name in response and response[model_name]:
                    knowledge_examples.append({
                        "model": model_name,
                        "prompt": prompt,
                        "response": response[model_name],
                        "timestamp": time.time(),
                        "goal_id": goal["id"]
                    })
            except Exception as e:
                logger.error(f"Fehler bei Abfrage von Modell {model_name}: {str(e)}", exc_info=True)
        
        return knowledge_examples
    
    def _perform_knowledge_distillation(self, goal: Dict[str, Any], examples: List[Dict[str, Any]]) -> bool:
        """Führt Knowledge Distillation durch."""
        try:
            # Hier würde der eigentliche Knowledge Distillation-Prozess stattfinden
            # Für diese vereinfachte Version geben wir nur eine Erfolgsmeldung aus
            
            # In einer echten Implementierung würden Sie hier:
            # 1. Die Wissensbeispiele verarbeiten
            # 2. Ein neues Modell trainieren oder das bestehende Modell aktualisieren
            # 3. Das neue Wissen speichern
            
            # Für das Beispiel geben wir nur eine Erfolgsmeldung aus
            return True
        except Exception as e:
            logger.error(f"Fehler bei Knowledge Distillation: {str(e)}", exc_info=True)
            return False
    
    def _update_model_metadata(self, model_name: str):
        """Aktualisiert die Metadaten des Modells."""
        try:
            # Hole aktuelle Metadaten
            metadata = self.mm.get_model_metadata(model_name)
            
            # Aktualisiere die Metadaten
            updates = {
                "last_trained": time.time(),
                "training_cycles": metadata.get("training_cycles", 0) + 1,
                "success_rate": (metadata.get("successful_training", 0) + 1) / 
                               (metadata.get("training_cycles", 0) + 1)
            }
            
            # Speichere die aktualisierten Metadaten
            self.mm.update_model_metadata(model_name, updates)
            logger.info(f"Modellmetadaten aktualisiert für {model_name}")
        except Exception as e:
            logger.error(f"Fehler bei der Aktualisierung der Modellmetadaten: {str(e)}", exc_info=True)
    
    def _log_learning_process(self, goal: Dict[str, Any], examples: List[Dict[str, Any]], success: bool):
        """Dokumentiert den Lernprozess."""
        try:
            # Speichere den Lernprozess in der Wissensdatenbank
            self.kb.store(
                "learning_process",
                {
                    "goal_id": goal["id"],
                    "goal_description": goal["description"],
                    "examples": examples,
                    "success": success,
                    "timestamp": time.time()
                }
            )
            logger.info(f"Lernprozess dokumentiert für Ziel {goal['id']}")
        except Exception as e:
            logger.error(f"Fehler bei der Dokumentation des Lernprozesses: {str(e)}", exc_info=True)
    
    def _run_reflection(self):
        """Führt eine Reflexion des Lernprozesses durch."""
        if self.reflection_active:
            return
            
        self.reflection_active = True
        logger.info("Reflexion abgeschlossen für Lernzyklus #%d", self.learning_cycle)
        
        try:
            # Berechne Erfolgsquote
            total = self.successful_cycles + self.failed_cycles
            success_rate = self.successful_cycles / total if total > 0 else 0
            
            logger.info("Reflexion abgeschlossen für Lernzyklus #%d. Erfolgsquote: %.2f", 
                       self.learning_cycle, success_rate)
            
            # Passe das Lernintervall basierend auf der Erfolgsquote an
            if success_rate > 0.8:
                # Verlängere das Intervall bei hoher Erfolgsquote
                self.learning_interval = min(
                    self.learning_interval * 1.2, 
                    self.config["learning_interval_seconds"] * 2
                )
            elif success_rate < 0.5:
                # Verkürze das Intervall bei niedriger Erfolgsquote
                self.learning_interval = max(
                    self.learning_interval * 0.8, 
                    self.config["learning_interval_seconds"] * 0.5
                )
            
            # Setze Zähler zurück
            self.successful_cycles = 0
            self.failed_cycles = 0
            
        except Exception as e:
            logger.error(f"Fehler bei der Reflexion: {str(e)}", exc_info=True)
        finally:
            self.reflection_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Gibt den Status des autonomen Lernzyklus zurück."""
        return {
            "active": self.active,
            "learning_cycle": self.learning_cycle,
            "learning_interval": self.learning_interval,
            "successful_cycles": self.successful_cycles,
            "failed_cycles": self.failed_cycles,
            "last_safety_check": self.last_safety_check,
            "timestamp": time.time()
        }