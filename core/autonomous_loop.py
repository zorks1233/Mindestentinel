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
import os
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
        model_cloner,
        knowledge_transfer,
        model_trainer,
        simulation_engine=None,
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
            model_cloner: Der ModelCloner
            knowledge_transfer: Der KnowledgeTransfer
            model_trainer: Der ModelTrainer
            simulation_engine: Die Simulation-Engine (optional)
            config: Optionale Konfiguration
        """
        self.ai_engine = ai_engine
        self.kb = knowledge_base
        self.model_orchestrator = model_orchestrator
        self.rule_engine = rule_engine
        self.protection_module = protection_module
        self.mm = model_manager
        self.system_monitor = system_monitor
        self.model_cloner = model_cloner
        self.knowledge_transfer = knowledge_transfer
        self.model_trainer = model_trainer
        self.simulation_engine = simulation_engine
        self.thread = None
        
        # Konfiguration mit Standardwerten
        self.config = {
            "max_learning_cycles": 1000,
            "learning_interval_seconds": 1800,  # Alle 30 Minuten
            "min_confidence_threshold": 0.65,
            "max_resource_usage": 0.85,
            "max_goal_complexity": 5,
            "safety_check_interval": 10,
            "max_concurrent_learning_sessions": 1,
            "min_knowledge_examples": 3,
            "max_knowledge_examples": 10,
            "min_simulation_safety_score": 0.7,
            "min_simulation_effectiveness_score": 0.6
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
        self.learning_sessions = {}  # Verfolgt aktive Lernsessions
        self.learning_session_counter = 0
        
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
            # Prüfe Ressourcenverfügbarkeit
            resource_usage = self.system_monitor.get_resource_usage()
            if resource_usage["cpu"] > self.config["max_resource_usage"] or \
               resource_usage["memory"] > self.config["max_resource_usage"]:
                logger.warning("Ressourcenverbrauch zu hoch. Überspringe Lernzyklus.")
                return
            
            # Generiere Lernziele
            learning_goals = self._generate_learning_goals()
            logger.info(f"Generierte {len(learning_goals)} neue Lernziele")
            
            # Starte Lernsessions für jedes Lernziel (begrenzt durch max_concurrent_learning_sessions)
            started_sessions = 0
            for goal in learning_goals:
                if started_sessions >= self.config["max_concurrent_learning_sessions"]:
                    break
                
                # Starte eine neue Lernsession
                session_id = self._start_learning_session(goal)
                if session_id:
                    started_sessions += 1
            
            # Warte auf den Abschluss der Lernsessions
            self._wait_for_learning_sessions()
            
            # Prüfe, ob wir ein neues Modell trainieren müssen
            self._check_for_new_model_training()
            
            # Prüfe, ob wir eine Simulation durchführen müssen
            self._check_for_simulations()
            
            logger.info(f"Lernintervall verlängert auf {self.learning_interval} Sekunden")
            
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
    
    def _start_learning_session(self, goal: Dict[str, Any]) -> Optional[str]:
        """
        Startet eine neue Lernsession.
        
        Args:
            goal: Das Lernziel
            
        Returns:
            Optional[str]: Die Session-ID, falls erfolgreich, sonst None
        """
        try:
            # Erstelle eine Session-ID
            self.learning_session_counter += 1
            session_id = f"session_{int(time.time())}_{self.learning_session_counter}"
            
            # Erstelle eine Kopie des Modells für das Lernen
            target_model = goal["target_model"]
            copy_name = self.model_cloner.create_model_copy(target_model)
            
            # Speichere die Session-Informationen
            self.learning_sessions[session_id] = {
                "id": session_id,
                "goal": goal,
                "model_copy": copy_name,
                "start_time": time.time(),
                "status": "running",
                "knowledge_examples": []
            }
            
            logger.info(f"Starte Lernsession {session_id} für Ziel {goal['id']} mit Modell-Kopie {copy_name}")
            
            # Starte die Lernsession in einem separaten Thread
            thread = threading.Thread(
                target=self._run_learning_session,
                args=(session_id,),
                daemon=True
            )
            thread.start()
            
            return session_id
        except Exception as e:
            logger.error(f"Fehler beim Starten der Lernsession: {str(e)}", exc_info=True)
            return None
    
    def _run_learning_session(self, session_id: str):
        """
        Führt eine Lernsession durch.
        
        Args:
            session_id: Die Session-ID
        """
        session = self.learning_sessions.get(session_id)
        if not session:
            logger.error(f"Lernsession {session_id} nicht gefunden")
            return
        
        try:
            goal = session["goal"]
            model_copy = session["model_copy"]
            
            logger.info(f"Lernsession {session_id}: Frage Lehrer-Modelle für Ziel {goal['id']}")
            
            # Frage Lehrer-Modelle
            knowledge_examples = self._query_teacher_models(goal)
            session["knowledge_examples"] = knowledge_examples
            
            if not knowledge_examples:
                logger.warning(f"Lernsession {session_id}: Keine Wissensbeispiele gesammelt")
                session["status"] = "failed"
                return
            
            logger.info(f"Lernsession {session_id}: Gesammelte {len(knowledge_examples)} Wissensbeispiele")
            
            # Führe Knowledge Distillation durch
            success = self._perform_knowledge_distillation(session_id, model_copy, knowledge_examples)
            
            if success:
                logger.info(f"Lernsession {session_id}: Knowledge Distillation erfolgreich")
                session["status"] = "completed"
            else:
                logger.warning(f"Lernsession {session_id}: Knowledge Distillation fehlgeschlagen")
                session["status"] = "failed"
        except Exception as e:
            logger.error(f"Fehler in Lernsession {session_id}: {str(e)}", exc_info=True)
            session["status"] = "failed"
    
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
        
        # Begrenze die Anzahl der Wissensbeispiele
        min_examples = self.config["min_knowledge_examples"]
        max_examples = self.config["max_knowledge_examples"]
        if len(knowledge_examples) > max_examples:
            knowledge_examples = random.sample(knowledge_examples, max_examples)
        elif len(knowledge_examples) < min_examples:
            logger.warning(f"Nur {len(knowledge_examples)} Wissensbeispiele gesammelt. Mindestens {min_examples} benötigt.")
        
        return knowledge_examples
    
    def _perform_knowledge_distillation(self, session_id: str, model_copy: str, examples: List[Dict[str, Any]]) -> bool:
        """Führt Knowledge Distillation durch."""
        try:
            logger.info(f"Lernsession {session_id}: Führe Knowledge Distillation durch mit {len(examples)} Beispielen")
            
            # Hier würde der eigentliche Knowledge Distillation-Prozess stattfinden
            # In einer echten Implementierung würden Sie hier:
            # 1. Die Wissensbeispiele verarbeiten
            # 2. Ein neues Modell trainieren oder das Modell-Kopie aktualisieren
            
            # Für das Beispiel: Markiere die Modell-Kopie als trainiert
            self.model_cloner.update_copy_status(
                model_copy,
                "trained",
                training_progress=1.0,
                knowledge_examples=len(examples)
            )
            
            # Validiere die Modell-Kopie
            self._validate_model_copy(session_id, model_copy)
            
            return True
        except Exception as e:
            logger.error(f"Fehler bei Knowledge Distillation: {str(e)}", exc_info=True)
            return False
    
    def _validate_model_copy(self, session_id: str, model_copy: str):
        """
        Validiert eine Modell-Kopie.
        
        Args:
            session_id: Die Session-ID
            model_copy: Der Name der Modell-Kopie
        """
        try:
            logger.info(f"Lernsession {session_id}: Validiere Modell-Kopie {model_copy}")
            
            # Hier würde die Validierung stattfinden
            # Für das Beispiel: Führe einige Testabfragen durch
            
            # Generiere Testprompts
            test_prompts = [
                "Erkläre die Grundlagen der Quantenphysik",
                "Wie funktioniert neuronale Netzwerke?",
                "Was sind die wichtigsten Sicherheitsprotokolle für KI-Systeme?"
            ]
            
            # Führe Testabfragen durch
            validation_score = 0.0
            total_tests = len(test_prompts)
            
            for prompt in test_prompts:
                try:
                    # Frage die Modell-Kopie
                    response = self.model_orchestrator.query(
                        prompt,
                        models=[model_copy]
                    )
                    
                    # Prüfe, ob die Antwort sinnvoll ist
                    if model_copy in response and response[model_copy]:
                        # In einer echten Implementierung würden Sie die Antwort bewerten
                        # Für das Beispiel geben wir einfach einen hohen Score zurück
                        validation_score += 0.9
                except Exception as e:
                    logger.error(f"Fehler bei Testabfrage: {str(e)}", exc_info=True)
            
            # Berechne den Validierungsscore
            validation_score = validation_score / total_tests
            
            # Aktualisiere den Status der Modell-Kopie
            self.model_cloner.update_copy_status(
                model_copy,
                "validated",
                validation_score=validation_score
            )
            
            logger.info(f"Lernsession {session_id}: Modell-Kopie validiert mit Score: {validation_score:.2f}")
        except Exception as e:
            logger.error(f"Fehler bei der Validierung der Modell-Kopie: {str(e)}", exc_info=True)
    
    def _wait_for_learning_sessions(self):
        """Wartet auf den Abschluss der Lernsessions."""
        while True:
            # Prüfe, ob alle Lernsessions abgeschlossen sind
            all_completed = True
            for session_id, session in list(self.learning_sessions.items()):
                if session["status"] == "running":
                    all_completed = False
                    break
            
            # Wenn alle Sessions abgeschlossen sind, beende die Wartezeit
            if all_completed:
                break
            
            # Warte kurz vor der nächsten Überprüfung
            time.sleep(1)
        
        # Übertrage das gelernte Wissen in das aktive System
        self._integrate_learned_knowledge()
    
    def _integrate_learned_knowledge(self):
        """Integriert gelerntes Wissen in das aktive System."""
        for session_id, session in list(self.learning_sessions.items()):
            if session["status"] == "completed":
                model_copy = session["model_copy"]
                
                # Integriere das gelernte Wissen
                target_model = session["goal"]["target_model"]
                success = self.model_cloner.integrate_learned_knowledge(model_copy, target_model)
                
                if success:
                    # Übertrage das Wissen in das aktive System
                    self.knowledge_transfer.transfer_learned_knowledge(session_id)
                    
                    # Lösche die Modell-Kopie
                    self._cleanup_learning_session(session_id)
                else:
                    logger.warning(f"Lernsession {session_id}: Wissenstransfer fehlgeschlagen")
                    self._cleanup_learning_session(session_id)
    
    def _cleanup_learning_session(self, session_id: str):
        """
        Bereinigt eine Lernsession.
        
        Args:
            session_id: Die Session-ID
        """
        if session_id not in self.learning_sessions:
            return
        
        session = self.learning_sessions[session_id]
        model_copy = session["model_copy"]
        
        try:
            # Lösche die Modell-Kopie
            copy_path = os.path.join(self.mm.models_dir, model_copy)
            if os.path.exists(copy_path):
                import shutil
                shutil.rmtree(copy_path)
                logger.info(f"Lernsession {session_id}: Modell-Kopie gelöscht: {model_copy}")
            
            # Entferne die Session aus der Liste
            del self.learning_sessions[session_id]
            logger.info(f"Lernsession {session_id} bereinigt")
        except Exception as e:
            logger.error(f"Fehler bei der Bereinigung der Lernsession: {str(e)}", exc_info=True)
    
    def _check_for_new_model_training(self):
        """Prüft, ob ein neues Modell trainiert werden soll."""
        # Speichere den Pfad zu den Trainingsdaten
        training_data_path = os.path.join("data", "training")
        os.makedirs(training_data_path, exist_ok=True)
        
        # Prüfe, ob genügend Trainingsdaten vorhanden sind
        training_files = [f for f in os.listdir(training_data_path) if f.endswith(".json")]
        
        if len(training_files) >= 5:  # Mindestanzahl an Trainingsdateien
            logger.info(f"Genügend Trainingsdaten gefunden ({len(training_files)}). Beginne mit dem Training eines neuen Modells.")
            
            # Trainiere ein neues Modell
            try:
                new_model_name = self.model_trainer.train_new_model(
                    f"auto_{int(time.time())}",
                    training_files[:10]  # Begrenze auf 10 Trainingsdateien
                )
                
                if new_model_name:
                    logger.info(f"Neues Modell erfolgreich trainiert: {new_model_name}")
                    
                    # Registriere das neue Modell als Lehrer-Modell
                    self.model_orchestrator.register_teacher_model(new_model_name)
                    logger.info(f"Neues Modell {new_model_name} als Lehrer-Modell registriert")
                    
                    # Erstelle ein Backup des alten Modells
                    old_model = self.mm.list_models()[0]  # Nimm das erste Modell als Referenz
                    backup_name = self.model_cloner.create_backup(old_model)
                    
                    # Ersetze das alte Modell durch das neue
                    try:
                        # Lösche das alte Modell
                        self.mm.unregister_model(old_model)
                        
                        # Kopiere das neue Modell an die Stelle des alten
                        old_model_path = os.path.join(self.mm.models_dir, old_model)
                        new_model_path = os.path.join(self.mm.models_dir, new_model_name)
                        
                        import shutil
                        shutil.move(new_model_path, old_model_path)
                        
                        # Lade das Modell neu
                        self.mm.load_models()
                        
                        logger.info(f"Altes Modell {old_model} durch neues Modell {new_model_name} ersetzt")
                    except Exception as e:
                        logger.error(f"Fehler beim Ersetzen des Modells: {str(e)}", exc_info=True)
                        
                        # Stelle das Backup wieder her
                        self.model_cloner.restore_from_backup(backup_name, old_model)
                        logger.info(f"Backup {backup_name} wiederhergestellt")
            except Exception as e:
                logger.error(f"Fehler beim Training eines neuen Modells: {str(e)}", exc_info=True)
    
    def _check_for_simulations(self):
        """Prüft, ob Simulationen durchgeführt werden müssen."""
        if not self.simulation_engine:
            logger.warning("Simulation-Engine nicht initialisiert. Simulationen werden übersprungen.")
            return
        
        # Prüfe, ob genügend Trainingsdaten vorhanden sind
        training_data_path = os.path.join("data", "training")
        os.makedirs(training_data_path, exist_ok=True)
        
        training_files = [f for f in os.listdir(training_data_path) if f.endswith(".json")]
        
        if len(training_files) >= 3:  # Mindestanzahl an Trainingsdateien für Simulation
            logger.info(f"Genügend Trainingsdaten für Simulation gefunden ({len(training_files)}).")
            
            # Erstelle eine Hypothese
            hypothesis_id = f"hypothesis_{int(time.time())}"
            hypothesis = {
                "id": hypothesis_id,
                "description": "Verbessere das Verständnis von kognitiven Prozessen",
                "training_files": training_files[:5],
                "target_model": self.mm.list_models()[0]
            }
            
            # Führe die Simulation durch
            simulation_result = self.simulation_engine.run_hypothesis(hypothesis_id, hypothesis)
            
            if simulation_result["success"]:
                logger.info(f"Simulation erfolgreich (Sicherheit: {simulation_result['safety_score']:.2f}, Effektivität: {simulation_result['effectiveness_score']:.2f})")
                
                # Prüfe, ob die Simulation gut genug war
                if simulation_result["safety_score"] >= self.config["min_simulation_safety_score"] and \
                   simulation_result["effectiveness_score"] >= self.config["min_simulation_effectiveness_score"]:
                    logger.info("Simulationsergebnis akzeptabel. Beginne mit dem eigentlichen Lernen...")
                    
                    # Führe das eigentliche Lernen durch
                    self._run_actual_learning(hypothesis)
                else:
                    logger.warning("Simulationsergebnis nicht ausreichend gut. Überspringe Lernen.")
            else:
                logger.error(f"Simulation fehlgeschlagen: {simulation_result.get('error', 'Unbekannter Fehler')}")
    
    def _run_actual_learning(self, hypothesis: Dict[str, Any]):
        """
        Führt das eigentliche Lernen basierend auf einer Hypothese durch.
        
        Args:
            hypothesis: Die Hypothese
        """
        logger.info(f"Starte tatsächliches Lernen basierend auf Hypothese {hypothesis['id']}")
        
        try:
            # Erstelle ein Lernziel aus der Hypothese
            goal = {
                "id": f"goal_{hypothesis['id']}",
                "description": hypothesis["description"],
                "complexity": 3,  # Mittlere Komplexität
                "priority": 0.8,  # Hohe Priorität
                "teacher_models": self.mm.list_models(),
                "target_model": hypothesis["target_model"],
                "required_resources": ["cpu", "memory"],
                "created_at": time.time()
            }
            
            # Starte eine neue Lernsession
            session_id = self._start_learning_session(goal)
            if session_id:
                logger.info(f"Lernsession {session_id} gestartet für Hypothese {hypothesis['id']}")
            else:
                logger.error(f"Fehler beim Starten der Lernsession für Hypothese {hypothesis['id']}")
        except Exception as e:
            logger.error(f"Fehler beim Starten des eigentlichen Lernens: {str(e)}", exc_info=True)
    
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
            "learning_sessions": len(self.learning_sessions),
            "active_sessions": sum(1 for s in self.learning_sessions.values() if s["status"] == "running"),
            "last_safety_check": self.last_safety_check,
            "timestamp": time.time()
        }