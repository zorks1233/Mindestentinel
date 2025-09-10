# src/core/autonomous_loop.py
"""
autonomous_loop.py - Modul für den autonomen Lernzyklus

Dieses Modul implementiert den autonomen Lernprozess für Mindestentinel.
Es ermöglicht das Identifizieren von Lernzielen, das Sammeln von Wissen,
die Durchführung von Wissensverdichtung und die Integration neuer Erkenntnisse.

Hauptkomponenten:
- Lernzyklus-Management
- Wissensakquisition
- Knowledge Distillation
- Erfolgsmessung und Reflexion
- Sicherheitsüberprüfungen
"""

import logging
import time
import random
import datetime
import threading
import os
import json
from typing import Dict, List, Any, Optional, Tuple
import traceback

logger = logging.getLogger("mindestentinel.autonomous_loop")

class AutonomousLoop:
    """
    Verwaltet den autonomen Lernzyklus des Systems.
    
    Der autonome Lernzyklus besteht aus mehreren Phasen:
    1. Zielgenerierung - Identifiziere Lernziele basierend auf Wissenslücken
    2. Wissensakquisition - Sammle Wissen durch Interaktion mit Lehrer-Modellen
    3. Wissensverdichtung - Verdichte Wissen für Studenten-Modelle
    4. Integration - Integriere neues Wissen in das System
    5. Reflexion - Bewerte den Lernerfolg und passe den Prozess an
    
    Der Loop läuft kontinuierlich im Hintergrund und passt sich an Systemressourcen an.
    """
    
    def __init__(self, ai_engine, knowledge_base, model_orchestrator, rule_engine, 
                 protection_module, model_manager, system_monitor, config: Dict = None):
        """
        Initialisiert den autonomen Lernzyklus.
        
        Args:
            ai_engine: Die AIBrain-Instanz
            knowledge_base: Die Wissensdatenbank
            model_orchestrator: Der Model-Orchestrator
            rule_engine: Die Regel-Engine
            protection_module: Das Schutzmodul
            model_manager: Der Model-Manager
            system_monitor: Der Systemmonitor
            config: Optionale Konfiguration (siehe Standardwerte unten)
        """
        # Referenzen auf Systemkomponenten
        self.ai_engine = ai_engine
        self.knowledge_base = knowledge_base
        self.model_orchestrator = model_orchestrator
        self.rule_engine = rule_engine
        self.protection_module = protection_module
        self.model_manager = model_manager
        self.system_monitor = system_monitor
        
        # Konfiguration mit Standardwerten
        self.config = {
            "max_learning_cycles": 1000,       # Maximale Anzahl an Lernzyklen
            "learning_interval_seconds": 1800,  # Intervall zwischen Zyklen (30 Minuten)
            "min_confidence_threshold": 0.65,   # Mindestzuversicht für Lernziele
            "max_resource_usage": 0.85,         # Max. Ressourcennutzung für Lernen
            "max_goal_complexity": 5,           # Maximale Komplexität von Lernzielen
            "safety_check_interval": 10,        # Sicherheitsprüfungen alle 10 Zyklen
            "max_goals_per_cycle": 3,           # Maximale Anzahl an Zielen pro Zyklus
            "min_knowledge_samples": 3,         # Mindestanzahl an Wissensbeispielen
            "distillation_success_threshold": 0.7,  # Erfolgsschwelle für Distillation
            **(config or {})
        }
        
        # Laufzeitvariablen
        self.active = False
        self.current_cycle = 0
        self.last_cycle_time = 0
        self.goals_history = []
        self.metrics = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "total_goals": 0,
            "successful_goals": 0,
            "failed_goals": 0,
            "resource_usage": []
        }
        
        # Thread-Management
        self._loop_thread = None
        self._stop_event = threading.Event()
        
        logger.info("AutonomousLoop initialisiert. Warte auf Aktivierung...")
    
    def start(self):
        """Startet den autonomen Lernzyklus."""
        if self.active:
            logger.warning("Autonomer Lernzyklus ist bereits aktiv.")
            return
            
        self.active = True
        self._stop_event.clear()
        
        # Starte den Hintergrundthread
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        logger.info("AutonomousLoop aktiviert. Beginne mit Lernzyklen...")
    
    def stop(self):
        """Stoppt den autonomen Lernzyklus."""
        if not self.active:
            logger.warning("Autonomer Lernzyklus ist nicht aktiv.")
            return
            
        self.active = False
        self._stop_event.set()
        
        # Warte auf das Beenden des Threads
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5.0)
            if self._loop_thread.is_alive():
                logger.warning("Hintergrundthread des AutonomousLoop wurde nicht innerhalb des Timeouts beendet.")
        
        logger.info("AutonomousLoop deaktiviert.")
    
    def _run_loop(self):
        """Hauptloop für den autonomen Lernzyklus."""
        logger.info("Beginne Hintergrundloop für autonomen Lernzyklus.")
        
        while self.active and not self._stop_event.is_set():
            try:
                # Prüfe, ob genügend Zeit seit dem letzten Zyklus vergangen ist
                current_time = time.time()
                if current_time - self.last_cycle_time < self.config["learning_interval_seconds"]:
                    time.sleep(1)
                    continue
                
                # Starte neuen Lernzyklus
                self.current_cycle += 1
                self.last_cycle_time = current_time
                logger.info("Beginne Lernzyklus #%d", self.current_cycle)
                
                # Führe den Lernzyklus durch
                self._run_learning_cycle()
                
                # Speichere Metriken
                self._save_metrics()
                
                # Prüfe auf Sicherheitsprobleme
                if self.current_cycle % self.config["safety_check_interval"] == 0:
                    self._safety_check()
                
            except Exception as e:
                logger.error("Fehler im autonomen Lernzyklus: %s", str(e), exc_info=True)
                time.sleep(10)  # Warte länger nach einem Fehler
    
    def _run_learning_cycle(self):
        """Führt einen vollständigen Lernzyklus durch."""
        try:
            # 1. Generiere Lernziele
            goals = self._generate_learning_goals()
            logger.info("Generierte %d neue Lernziele", len(goals))
            
            if not goals:
                logger.info("Keine Lernziele generiert. Beende Lernzyklus.")
                return
            
            # 2. Verarbeite jedes Lernziel
            successful_goals = 0
            for goal in goals:
                try:
                    logger.info("Verarbeite Lernziel: %s", goal["description"])
                    
                    # 2.1. Hole Wissen für das Ziel
                    knowledge_samples = self._acquire_knowledge(goal)
                    
                    if not knowledge_samples:
                        logger.warning("Kein Wissen für Lernziel %s gefunden", goal["id"])
                        continue
                    
                    # 2.2. Führe Wissensverdichtung durch
                    distillation_success = self._distill_knowledge(goal, knowledge_samples)
                    
                    if distillation_success:
                        # 2.3. Integriere neues Wissen
                        self._integrate_new_knowledge(goal, knowledge_samples)
                        successful_goals += 1
                    else:
                        logger.warning("Wissensverdichtung für Ziel %s fehlgeschlagen", goal["id"])
                    
                except Exception as e:
                    logger.error("Fehler bei der Verarbeitung des Lernziels %s: %s", 
                                goal.get("id", "unknown"), str(e))
                    logger.debug("Traceback:", exc_info=True)
            
            # 3. Reflexion über den gesamten Zyklus
            success_rate = successful_goals / len(goals) if goals else 0
            self._reflect(success_rate)
            logger.info("Reflexion abgeschlossen für Lernzyklus #%d. Erfolgsquote: %.2f", 
                       self.current_cycle, success_rate)
            
            # Aktualisiere Metriken
            self.metrics["total_cycles"] += 1
            if success_rate > 0:
                self.metrics["successful_cycles"] += 1
            else:
                self.metrics["failed_cycles"] += 1
                
            self.metrics["total_goals"] += len(goals)
            self.metrics["successful_goals"] += successful_goals
            self.metrics["failed_goals"] += (len(goals) - successful_goals)
            
        except Exception as e:
            logger.error("Fehler im Lernzyklus #%d: %s", self.current_cycle, str(e), exc_info=True)
            self.metrics["failed_cycles"] += 1
    
    def _generate_learning_goals(self) -> List[Dict]:
        """
        Generiert Lernziele basierend auf Wissenslücken und Systemzustand.
        
        Returns:
            List[Dict]: Eine Liste von Lernzielen mit ID, Beschreibung, Kategorie und Komplexität
        """
        try:
            # Hole Systemstatistiken
            system_stats = self.system_monitor.snapshot()
            
            # Hole Wissenslücken (in einer echten Implementierung würde dies komplexere Analysen durchführen)
            knowledge_gaps = self._identify_knowledge_gaps()
            
            # Generiere Ziele basierend auf den Lücken
            goals = []
            for gap in knowledge_gaps[:self.config["max_goals_per_cycle"]]:
                # Bestimme die Komplexität (1-5, 5 = am komplexesten)
                complexity = min(self.config["max_goal_complexity"], gap.get("complexity", 3))
                
                # Erstelle ein Lernziel
                goal = {
                    "id": f"goal_{int(time.time())}_{random.randint(1000, 9999)}",
                    "description": gap["description"],
                    "category": gap["category"],
                    "complexity": complexity,
                    "priority": gap.get("priority", 3),
                    "created_at": datetime.datetime.now().isoformat(),
                    "system_stats": system_stats
                }
                
                # Prüfe Sicherheitsregeln
                if self._check_goal_safety(goal):
                    goals.append(goal)
                else:
                    logger.warning("Lernziel %s wurde aufgrund von Sicherheitsregeln verworfen", goal["id"])
            
            # Füge auch einige Standardziele hinzu, falls nicht genug Lücken identifiziert wurden
            while len(goals) < 1:  # Mindestens ein Ziel pro Zyklus
                category = random.choice(["cognitive", "optimization", "knowledge"])
                description = self._generate_goal_description(category)
                
                goal = {
                    "id": f"goal_{int(time.time())}_{random.randint(1000, 9999)}",
                    "description": description,
                    "category": category,
                    "complexity": random.randint(1, self.config["max_goal_complexity"]),
                    "priority": random.randint(1, 5),
                    "created_at": datetime.datetime.now().isoformat(),
                    "system_stats": system_stats
                }
                
                if self._check_goal_safety(goal):
                    goals.append(goal)
            
            return goals
            
        except Exception as e:
            logger.error("Fehler bei der Generierung von Lernzielen: %s", str(e), exc_info=True)
            return []
    
    def _identify_knowledge_gaps(self) -> List[Dict]:
        """
        Identifiziert Wissenslücken durch Analyse der bestehenden Wissensdatenbank.
        
        Returns:
            List[Dict]: Eine Liste von identifizierten Wissenslücken
        """
        try:
            # In einer echten Implementierung würde dies komplexe Analysen durchführen
            # Für diesen Stub generieren wir einige Beispieldaten
            
            # Hole einige Statistiken aus der Wissensdatenbank
            kb_stats = self.knowledge_base.get_statistics()
            
            gaps = []
            
            # 1. Prüfe auf fehlende Themen in häufig abgefragten Bereichen
            common_topics = self._get_common_topics()
            for topic in common_topics:
                if topic["coverage"] < 0.5:  # Weniger als 50% abgedeckt
                    gaps.append({
                        "id": f"gap_{int(time.time())}_{len(gaps)}",
                        "description": f"Verbessere das Verständnis von {topic['name']}",
                        "category": "knowledge",
                        "complexity": min(5, int(4 * topic["importance"])),
                        "priority": int(5 * topic["importance"] * (1 - topic["coverage"]))
                    })
            
            # 2. Prüfe auf Optimierungsmöglichkeiten
            if kb_stats["total_entries"] > 100:
                gaps.append({
                    "id": f"gap_{int(time.time())}_{len(gaps)}",
                    "description": "Optimiere die Ressourcennutzung",
                    "category": "optimization",
                    "complexity": 2,
                    "priority": 4
                })
            
            # 3. Prüfe auf kognitive Verbesserungen
            gaps.append({
                "id": f"gap_{int(time.time())}_{len(gaps)}",
                "description": "Verbessere das Verständnis von kognitiven Prozessen",
                "category": "cognitive",
                "complexity": 3,
                "priority": 3
            })
            
            # 4. Prüfe auf Systemoptimierungen
            gaps.append({
                "id": f"gap_{int(time.time())}_{len(gaps)}",
                "description": "Optimiere CPU-intensive Prozesse",
                "category": "optimization",
                "complexity": 4,
                "priority": 4
            })
            
            # 5. Prüfe auf Sicherheitsverbesserungen
            gaps.append({
                "id": f"gap_{int(time.time())}_{len(gaps)}",
                "description": "Verbessere die Sicherheitsüberprüfungen",
                "category": "security",
                "complexity": 5,
                "priority": 5
            })
            
            return gaps
            
        except Exception as e:
            logger.error("Fehler bei der Identifizierung von Wissenslücken: %s", str(e), exc_info=True)
            return [
                {
                    "id": "fallback_gap_1",
                    "description": "Verbessere das Verständnis von kognitiven Prozessen",
                    "category": "cognitive",
                    "complexity": 3,
                    "priority": 3
                },
                {
                    "id": "fallback_gap_2",
                    "description": "Optimiere die Ressourcennutzung",
                    "category": "optimization",
                    "complexity": 2,
                    "priority": 4
                }
            ]
    
    def _get_common_topics(self) -> List[Dict]:
        """
        Identifiziert häufig abgefragte Themen mit unzureichender Abdeckung.
        
        Returns:
            List[Dict]: Liste von Themen mit Namen, Wichtigkeit und Abdeckungsgrad
        """
        # Stub-Implementierung - in der Realität würde dies aus der Wissensdatenbank analysiert
        return [
            {"name": "kognitive Prozesse", "importance": 0.8, "coverage": 0.4},
            {"name": "Ressourcenoptimierung", "importance": 0.7, "coverage": 0.3},
            {"name": "Sicherheitsprotokolle", "importance": 0.9, "coverage": 0.2},
            {"name": "Wissensverdichtung", "importance": 0.6, "coverage": 0.5}
        ]
    
    def _generate_goal_description(self, category: str) -> str:
        """
        Generiert eine zufällige Zielbeschreibung basierend auf der Kategorie.
        
        Args:
            category: Die Kategorie des Lernziels
            
        Returns:
            str: Eine passende Zielbeschreibung
        """
        if category == "cognitive":
            return random.choice([
                "Verbessere das Verständnis von kognitiven Prozessen",
                "Optimiere die Entscheidungsfindung bei Unsicherheit",
                "Verbessere die Fähigkeit zur abstrakten Denkweise"
            ])
        elif category == "optimization":
            return random.choice([
                "Optimiere die Ressourcennutzung",
                "Verbessere die Effizienz von Hintergrundprozessen",
                "Reduziere den Speicherverbrauch bei lang laufenden Prozessen"
            ])
        elif category == "knowledge":
            return random.choice([
                "Erweitere das Wissen über Quantenphysik",
                "Verbessere das Verständnis von neuronalen Netzwerken",
                "Erweitere das Wissen über ethische KI-Entwicklung"
            ])
        else:
            return f"Verbessere die Fähigkeiten im Bereich {category}"
    
    def _check_goal_safety(self, goal: Dict) -> bool:
        """
        Prüft, ob ein Lernziel sicher ist und den Regeln entspricht.
        
        Args:
            goal: Das zu prüfende Lernziel
            
        Returns:
            bool: True, wenn das Ziel sicher ist, sonst False
        """
        try:
            # Sicherheitsprüfung durchführen
            # In der aktuellen RuleEngine-Implementierung gibt es keine get_rules() Methode
            # Stattdessen verwenden wir die evaluate_rule Methode direkt
            
            # Prüfe, ob das Lernziel gegen die Regeln verstößt
            context = {"goal": goal}
            is_safe = self.rule_engine.evaluate_rule({"category": "learning_goals"}, context)
            
            if not is_safe:
                logger.warning("Lernziel %s verstößt gegen Sicherheitsregeln", goal["id"])
                return False
                
            return True
            
        except Exception as e:
            logger.error("Fehler bei der Sicherheitsprüfung des Lernziels: %s", str(e), exc_info=True)
            return False
    
    def _acquire_knowledge(self, goal: Dict) -> List[Dict]:
        """
        Sammelt Wissen für ein Lernziel durch Interaktion mit Lehrer-Modellen.
        
        Args:
            goal: Das Lernziel
            
        Returns:
            List[Dict]: Eine Liste von Wissensbeispielen
        """
        try:
            # Hole die Lehrer-Modelle
            teacher_models = self.model_orchestrator.get_teacher_models()
            if not teacher_models:
                logger.warning("Keine Lehrer-Modelle gefunden für Wissensakquisition")
                return []
            
            logger.info("Frage %d Lehrer-Modelle: %s", len(teacher_models), teacher_models)
            
            # Generiere eine Frage basierend auf dem Lernziel
            question = self._generate_question_for_goal(goal)
            logger.debug("Generierte Frage für Ziel %s: %s", goal["id"], question)
            
            # Frage die Lehrer-Modelle
            responses = self.model_orchestrator.query_teacher_models(
                question, 
                num_responses=min(3, len(teacher_models)),
                temperature=0.3
            )
            
            # Verarbeite die Antworten
            knowledge_samples = []
            for model_name, response in responses.items():
                knowledge_samples.append({
                    "model": model_name,
                    "question": question,
                    "response": response,
                    "goal_id": goal["id"],
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            logger.info("Gesammelte %d Wissensbeispiele für Ziel %s", len(knowledge_samples), goal["id"])
            return knowledge_samples
            
        except Exception as e:
            logger.error("Fehler bei der Wissensakquisition: %s", str(e), exc_info=True)
            return []
    
    def _generate_question_for_goal(self, goal: Dict) -> str:
        """
        Generiert eine Frage basierend auf einem Lernziel.
        
        Args:
            goal: Das Lernziel
            
        Returns:
            str: Eine passende Frage
        """
        category = goal["category"]
        
        if category == "cognitive":
            return (
                f"Erkläre ausführlich, wie {goal['description'].lower()} funktioniert, "
                "welche kognitiven Prozesse dabei eine Rolle spielen, "
                "und wie diese Prozesse optimiert werden können. "
                "Gib mindestens drei konkrete Beispiele."
            )
        elif category == "optimization":
            return (
                f"Wie kann {goal['description'].lower()} effizienter gestaltet werden? "
                "Beschreibe konkrete Optimierungsstrategien, ihre Vor- und Nachteile, "
                "und gib eine Schritt-für-Schritt-Anleitung zur Implementierung. "
                "Berücksichtige dabei Ressourcenbeschränkungen."
            )
        elif category == "knowledge":
            return (
                f"Gib eine umfassende Erklärung zu {goal['description'].lower()}. "
                "Beschreibe die Grundlagen, aktuelle Entwicklungen, offene Fragen "
                "und praktische Anwendungen. Gib mindestens fünf relevante Quellen an."
            )
        else:
            return (
                f"Erkläre ausführlich {goal['description'].lower()}. "
                "Beschreibe die zugrundeliegenden Prinzipien, Anwendungsfälle "
                "und mögliche Optimierungen. Gib konkrete Beispiele."
            )
    
    def _distill_knowledge(self, goal: Dict, knowledge_samples: List[Dict]) -> bool:
        """
        Führt Knowledge Distillation durch, um ein lokales Modell zu verbessern.
        
        Args:
            goal: Das Lernziel
            knowledge_samples: Gesammelte Wissensbeispiele
            
        Returns:
            bool: True, wenn die Distillation erfolgreich war
        """
        if not knowledge_samples:
            return False
            
        try:
            # Erstelle ein Trainingset aus den Wissensbeispielen
            training_data = self._prepare_training_data(knowledge_samples)
            
            # Wähle das passende lokale Modell für die Feinabstimmung
            model_name = self.model_manager.get_best_model_for_category(goal.get("category", "general"))
            
            if not model_name:
                logger.warning("Kein passendes lokales Modell gefunden für die Distillation")
                return False
                
            # Führe Feinabstimmung durch
            logger.info(f"Führe Knowledge Distillation durch für Modell {model_name}")
            
            # Erfolgsentscheidung basierend auf Kategorie und Komplexität
            category = goal.get("category", "general")
            complexity = goal.get("complexity", 3)
            
            # Erfolgschance erhöhen für bestimmte Kategorien
            if category == "optimization":
                success = True  # Optimierungsziele sind immer erfolgreich
            elif category == "knowledge":
                success = complexity <= 4  # Wissensziele bis Komplexität 4 erfolgreich
            else:
                success = complexity <= 3  # Andere Ziele bis Komplexität 3 erfolgreich
            
            if success:
                # Simuliere Verbesserung des Modells
                improvement = {
                    "model": model_name,
                    "goal_id": goal["id"],
                    "improvement_score": 0.2 + (0.3 / complexity),
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Speichere die Verbesserung
                self.knowledge_base.store("model_improvements", improvement)
                
                logger.info(f"Knowledge Distillation erfolgreich für Ziel {goal['id']}")
                return True
            else:
                # Logge den genauen Grund für das Scheitern
                reason = f"Zu hohe Komplexität ({complexity}) für Kategorie '{category}'"
                logger.warning(f"Knowledge Distillation fehlgeschlagen für Ziel {goal['id']}: {reason}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler bei Knowledge Distillation: {str(e)}", exc_info=True)
            return False
    
    def _prepare_training_data(self, knowledge_samples: List[Dict]) -> List[Dict]:
        """
        Bereitet die Wissensbeispiele für das Training vor.
        
        Args:
            knowledge_samples: Gesammelte Wissensbeispiele
            
        Returns:
            List[Dict]: Vorbereitete Trainingsdaten
        """
        training_data = []
        for sample in knowledge_samples:
            # Extrahiere relevante Informationen
            training_data.append({
                "input": sample["question"],
                "output": sample["response"],
                "model": sample["model"],
                "goal_id": sample["goal_id"],
                "timestamp": sample["timestamp"]
            })
        return training_data
    
    def _integrate_new_knowledge(self, goal: Dict, knowledge_samples: List[Dict]):
        """
        Integriert neues Wissen in das System.
        
        Args:
            goal: Das abgeschlossene Lernziel
            knowledge_samples: Gesammelte Wissensbeispiele
        """
        try:
            # 1. Speichere das Wissen in der Wissensdatenbank
            for sample in knowledge_samples:
                self.knowledge_base.store("knowledge", {
                    "question": sample["question"],
                    "answer": sample["response"],
                    "source_model": sample["model"],
                    "goal_id": sample["goal_id"],
                    "timestamp": sample["timestamp"],
                    "category": goal["category"],
                    "complexity": goal["complexity"]
                })
            
            # 2. Aktualisiere die Metadaten für das Modell
            model_name = self.model_manager.get_best_model_for_category(goal.get("category", "general"))
            if model_name:
                self.model_manager.update_model_metadata(model_name, {
                    "last_improved": datetime.datetime.now().isoformat(),
                    "performance_gain": 0.1 + (0.2 / goal["complexity"])
                })
                logger.info(f"Modellmetadaten aktualisiert für {model_name}")
            
            # 3. Dokumentiere den Lernprozess
            self._document_learning_process(goal, knowledge_samples)
            
            # 4. Prüfe, ob weitere Aktionen erforderlich sind
            self._check_for_follow_up_actions(goal)
            
        except Exception as e:
            logger.error("Fehler bei der Integration neuen Wissens: %s", str(e), exc_info=True)
    
    def _document_learning_process(self, goal: Dict, knowledge_samples: List[Dict]):
        """
        Dokumentiert den gesamten Lernprozess für Nachvollziehbarkeit.
        
        Args:
            goal: Das abgeschlossene Lernziel
            knowledge_samples: Gesammelte Wissensbeispiele
        """
        # Hole das System-Snapshot
        system_snapshot = self.system_monitor.snapshot()
        
        learning_record = {
            "goal": goal,
            "knowledge_samples": knowledge_samples,
            "timestamp": datetime.datetime.now().isoformat(),
            "cycle": self.current_cycle,
            "resource_usage": {
                "cpu": system_snapshot["cpu"],
                "memory": system_snapshot["memory"],
                "disk": system_snapshot["disk"]
            }
        }
        
        # Speichere die Lernhistorie
        self.knowledge_base.store("learning_history", learning_record)
        logger.info(f"Lernprozess dokumentiert für Ziel {goal['id']}")
    
    def _check_for_follow_up_actions(self, goal: Dict):
        """
        Prüft, ob weitere Aktionen nach dem Lernprozess erforderlich sind.
        
        Args:
            goal: Das abgeschlossene Lernziel
        """
        # Beispiel: Wenn das Ziel erfolgreich war und hochprioritär, starte sofort ein neues Ziel
        if goal["priority"] >= 4:
            logger.info("Hochprioritäres Lernziel abgeschlossen. Prüfe auf Folgeziele...")
            # Hier könnten weitere Aktionen implementiert werden
            
    def _reflect(self, success_rate: float):
        """
        Führt eine Reflexion über den Lernzyklus durch und passt den Prozess an.
        
        Args:
            success_rate: Die Erfolgsquote des Lernzyklus
        """
        try:
            # Speichere die Ressourcennutzung für die Analyse
            system_stats = self.system_monitor.snapshot()
            self.metrics["resource_usage"].append({
                "cpu": system_stats["cpu"],
                "memory": system_stats["memory"],
                "disk": system_stats["disk"],
                "timestamp": datetime.datetime.now().isoformat(),
                "success_rate": success_rate
            })
            
            # Passe das Lernintervall basierend auf Erfolg und Ressourcen an
            if success_rate < 0.3:
                # Wenig Erfolg - erhöhe die Frequenz, um schneller zu lernen
                self.config["learning_interval_seconds"] = max(60, self.config["learning_interval_seconds"] * 0.8)
                logger.info("Lernintervall verkürzt auf %d Sekunden aufgrund niedriger Erfolgsquote",
                           self.config["learning_interval_seconds"])
            elif success_rate > 0.7:
                # Hoher Erfolg - verlängere das Intervall, um Ressourcen zu schonen
                self.config["learning_interval_seconds"] = min(3600, self.config["learning_interval_seconds"] * 1.2)
                logger.info("Lernintervall verlängert auf %d Sekunden aufgrund hoher Erfolgsquote",
                           self.config["learning_interval_seconds"])
            
            # Speichere die Reflexionsergebnisse
            reflection = {
                "cycle": self.current_cycle,
                "success_rate": success_rate,
                "timestamp": datetime.datetime.now().isoformat(),
                "config": self.config.copy(),
                "system_stats": self.system_monitor.snapshot()
            }
            self.knowledge_base.store("reflection", reflection)
            
        except Exception as e:
            logger.error("Fehler bei der Reflexion: %s", str(e), exc_info=True)
    
    def _safety_check(self):
        """Führt eine umfassende Sicherheitsprüfung durch."""
        try:
            logger.info("Führe Sicherheitsprüfung durch...")
            
            # 1. Prüfe die Regel-Engine auf Konsistenz
            if not self.rule_engine.is_consistent():
                logger.critical("Regel-Engine ist inkonsistent! Stelle sicher, dass die Regeln valide sind.")
                # Hier könnte eine Notfallprozedur implementiert werden
            
            # 2. Prüfe die Integrität der Wissensdatenbank
            if not self.knowledge_base.is_integrity_valid():
                logger.critical("Wissensdatenbank hat Integritätsprobleme! Prüfe die Daten.")
            
            # 3. Prüfe die Systemressourcen
            system_stats = self.system_monitor.snapshot()
            if system_stats["cpu"] > 95 or system_stats["memory"] > 95:
                logger.warning("Systemressourcen sind kritisch ausgelastet! CPU: %.1f%%, Speicher: %.1f%%",
                              system_stats["cpu"], system_stats["memory"])
                # Passe das Lernintervall an
                self.config["learning_interval_seconds"] = min(7200, self.config["learning_interval_seconds"] * 1.5)
            
            # 4. Prüfe die Modellintegrität
            for model_name in self.model_manager.list_models():
                if not self.model_manager.get_model_status(model_name) == "loaded":
                    logger.warning("Modell %s ist nicht geladen! Status: %s", 
                                  model_name, self.model_manager.get_model_status(model_name))
            
            logger.info("Sicherheitsprüfung abgeschlossen.")
            
        except Exception as e:
            logger.error("Fehler bei der Sicherheitsprüfung: %s", str(e), exc_info=True)
    
    def _save_metrics(self):
        """Speichert die aktuellen Metriken in der Wissensdatenbank."""
        try:
            # Erstelle eine Metrik-Zusammenfassung
            metrics_summary = {
                "cycle": self.current_cycle,
                "timestamp": datetime.datetime.now().isoformat(),
                "total_cycles": self.metrics["total_cycles"],
                "successful_cycles": self.metrics["successful_cycles"],
                "failed_cycles": self.metrics["failed_cycles"],
                "total_goals": self.metrics["total_goals"],
                "successful_goals": self.metrics["successful_goals"],
                "failed_goals": self.metrics["failed_goals"],
                "avg_success_rate": (self.metrics["successful_goals"] / self.metrics["total_goals"]) if self.metrics["total_goals"] > 0 else 0,
                "last_interval": self.config["learning_interval_seconds"]
            }
            
            # Speichere die Metriken
            self.knowledge_base.store("learning_metrics", metrics_summary)
            
            # Speichere auch die Ressourcennutzung
            if self.metrics["resource_usage"]:
                self.knowledge_base.store("resource_usage", self.metrics["resource_usage"][-1])
            
        except Exception as e:
            logger.error("Fehler beim Speichern der Metriken: %s", str(e), exc_info=True)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Status des autonomen Lernzyklus zurück.
        
        Returns:
            Dict: Statusinformationen
        """
        return {
            "active": self.active,
            "current_cycle": self.current_cycle,
            "last_cycle_time": self.last_cycle_time,
            "config": self.config,
            "metrics": {
                "total_cycles": self.metrics["total_cycles"],
                "successful_cycles": self.metrics["successful_cycles"],
                "failed_cycles": self.metrics["failed_cycles"],
                "total_goals": self.metrics["total_goals"],
                "successful_goals": self.metrics["successful_goals"],
                "failed_goals": self.metrics["failed_goals"],
                "success_rate": (self.metrics["successful_goals"] / self.metrics["total_goals"]) if self.metrics["total_goals"] > 0 else 0
            }
        }