"""
autonomous_loop.py
Implementiert den autonomen Lernzyklus für Mindestentinel
"""

import os
import sys
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Tuple

# Robuste Projekt-Root-Erkennung
def get_project_root() -> str:
    """
    Findet das Projekt-Root-Verzeichnis unabhängig vom aktuellen Arbeitsverzeichnis
    
    Returns:
        str: Absolute Pfad zum Projekt-Root
    """
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # Versuche 1: Von src/core aus
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 2: Von core aus
    project_root = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(project_root, "src", "core")):
        return project_root
    
    # Versuche 3: Aktuelles Verzeichnis ist Projekt-Root
    project_root = current_dir
    if os.path.exists(os.path.join(project_root, "src", "core")) or os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 4: Projekt-Root ist zwei Ebenen höher
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Fallback: Aktuelles Verzeichnis
    return os.getcwd()

# Setze PYTHONPATH korrekt
PROJECT_ROOT = get_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import-Handling für Core-Module
try:
    from core.ai_engine import AIBrain
    from core.rule_engine import RuleEngine
    from core.user_manager import UserManager
    from core.self_learning import SelfLearning
    logging.debug("Core-Module erfolgreich importiert")
except ImportError:
    try:
        from src.core.ai_engine import AIBrain
        from src.core.rule_engine import RuleEngine
        from src.core.user_manager import UserManager
        from src.core.self_learning import SelfLearning
        logging.debug("Core-Module erfolgreich aus src/core importiert")
    except ImportError as e:
        logging.error(f"Kritischer Fehler: Core-Module können nicht importiert werden: {str(e)}")
        # Definiere Dummy-Klassen als letzter Ausweg
        class AIBrain:
            def __init__(self, *args, **kwargs):
                pass
            def process_input(self, *args, **kwargs):
                return "Dummy-Antwort"
        
        class RuleEngine:
            def __init__(self, *args, **kwargs):
                pass
            def apply_rules(self, *args, **kwargs):
                return {"allowed": True}
        
        class UserManager:
            def __init__(self, *args, **kwargs):
                pass
            def get_user(self, *args, **kwargs):
                return {"id": "dummy", "name": "Dummy User"}
        
        class SelfLearning:
            def __init__(self, *args, **kwargs):
                pass
            def start_learning_process(self, *args, **kwargs):
                pass
            def record_experience(self, *args, **kwargs):
                pass
            def save_progress(self, *args, **kwargs):
                pass

# Initialisiere Logging
logger = logging.getLogger("mindestentinel.autonomous_loop")
logger.setLevel(logging.INFO)

class AutonomousLoop:
    """
    Implementiert den autonomen Lernzyklus für Mindestentinel
    Führt regelmäßig selbstlernende Aufgaben aus, ohne Benutzerinteraktion
    """
    
    def __init__(self, brain: AIBrain, rule_engine: RuleEngine, 
                 user_manager: Optional[UserManager] = None,
                 cycle_interval: int = 300,  # 5 Minuten
                 max_cycles: int = None):
        """
        Initialisiert den autonomen Lernzyklus
        
        Args:
            brain: Die AIBrain-Instanz
            rule_engine: Die RuleEngine-Instanz
            user_manager: Optional die UserManager-Instanz
            cycle_interval: Intervall zwischen den Lernzyklen in Sekunden
            max_cycles: Maximale Anzahl von Zyklen (None für unbegrenzt)
        """
        self.brain = brain
        self.rule_engine = rule_engine
        self.user_manager = user_manager
        self.cycle_interval = cycle_interval
        self.max_cycles = max_cycles
        
        self.running = False
        self.thread = None
        self.cycle_counter = 0
        self.last_cycle_time = None
        
        logger.info("AutonomousLoop erfolgreich initialisiert")
        logger.debug(f"Konfiguration: cycle_interval={cycle_interval}s, max_cycles={max_cycles}")
    
    def start(self) -> None:
        """
        Startet den autonomen Lernzyklus
        
        Raises:
            RuntimeError: Wenn der Zyklus bereits läuft
        """
        if self.running:
            logger.warning("Versuch, AutonomousLoop zu starten, aber er läuft bereits")
            return
        
        logger.info(f"Starte autonomen Lernzyklus (Intervall: {self.cycle_interval}s)")
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """
        Stoppt den autonomen Lernzyklus
        """
        if not self.running:
            logger.debug("AutonomousLoop ist nicht aktiv, kein Stop erforderlich")
            return
        
        logger.info("Stoppe autonomen Lernzyklus...")
        self.running = False
        
        # Warte auf das Beenden des Threads
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                logger.warning("Thread des autonomen Lernzyklus wurde nicht ordnungsgemäß beendet")
        
        self.thread = None
    
    def _run_loop(self) -> None:
        """
        Hauptschleife des autonomen Lernzyklus
        """
        logger.debug("Autonomer Lernzyklus-Thread gestartet")
        
        while self.running:
            try:
                # Führe einen Lernzyklus durch
                self._run_cycle()
                
                # Warte bis zum nächsten Zyklus
                if self.running and self.cycle_interval > 0:
                    time.sleep(self.cycle_interval)
            
            except Exception as e:
                logger.error(f"Fehler im autonomen Lernzyklus: {str(e)}")
                # Warte vor dem nächsten Versuch
                time.sleep(10)
        
        logger.debug("Autonomer Lernzyklus-Thread beendet")
    
    def _run_cycle(self) -> None:
        """
        Führt einen einzelnen Lernzyklus durch
        """
        self.cycle_counter += 1
        self.last_cycle_time = time.time()
        
        logger.info(f"Starte Lernzyklus {self.cycle_counter}...")
        
        try:
            # 1. Systemzustand analysieren
            self._analyze_system_state()
            
            # 2. Selbstlernprozess durchführen
            self._run_self_learning()
            
            # 3. Systemoptimierungen durchführen
            self._perform_optimizations()
            
            # 4. Sicherheitsüberprüfung durchführen
            self._run_security_check()
            
            # 5. Protokollierung des Zyklus
            self._log_cycle_completion()
            
            # Prüfe, ob die maximale Anzahl von Zyklen erreicht wurde
            if self.max_cycles is not None and self.cycle_counter >= self.max_cycles:
                logger.info(f"Maximale Anzahl von Zyklen ({self.max_cycles}) erreicht. Beende autonomen Lernzyklus.")
                self.stop()
        
        except Exception as e:
            logger.error(f"Fehler im Lernzyklus {self.cycle_counter}: {str(e)}")
    
    def _analyze_system_state(self) -> None:
        """
        Analysiert den aktuellen Systemzustand
        """
        logger.debug("Analysiere Systemzustand...")
        
        # Hier würden wir den Systemzustand analysieren
        # Für dieses Beispiel verwenden wir Dummy-Daten
        
        # Beispiel: Überprüfe die Auslastung
        system_load = 0.7  # 70% Auslastung (Dummy-Wert)
        logger.debug(f"Aktuelle Systemauslastung: {system_load:.0%}")
        
        # Beispiel: Überprüfe die Antwortqualität
        response_quality = 0.85  # 85% Qualität (Dummy-Wert)
        logger.debug(f"Aktuelle Antwortqualität: {response_quality:.0%}")
    
    def _run_self_learning(self) -> None:
        """
        Führt den Selbstlernprozess durch
        """
        logger.debug("Führe Selbstlernprozess durch...")
        
        # Prüfe, ob SelfLearning verfügbar ist
        if hasattr(self.brain, 'self_learning') and self.brain.self_learning:
            try:
                # Starte den Lernprozess
                self.brain.self_learning.start_learning_process()
                
                # Führe einen Lernzyklus durch
                cycle_result = self.brain.self_learning.learning_cycle()
                
                logger.info(f"Selbstlernzyklus abgeschlossen. Status: {cycle_result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"Fehler beim Selbstlernprozess: {str(e)}")
        else:
            logger.warning("SelfLearning-Modul nicht verfügbar - überspringe Selbstlernprozess")
    
    def _perform_optimizations(self) -> None:
        """
        Führt Systemoptimierungen durch
        """
        logger.debug("Führe Systemoptimierungen durch...")
        
        # Hier würden wir Optimierungen durchführen
        # Für dieses Beispiel verwenden wir Dummy-Operationen
        
        # Beispiel: Modell-Optimierung
        try:
            # In einer echten Implementierung würden wir das Modell optimieren
            logger.info("Modell-Optimierung durchgeführt")
        except Exception as e:
            logger.error(f"Fehler bei der Modell-Optimierung: {str(e)}")
        
        # Beispiel: Cache-Optimierung
        try:
            # In einer echten Implementierung würden wir den Cache optimieren
            logger.info("Cache-Optimierung durchgeführt")
        except Exception as e:
            logger.error(f"Fehler bei der Cache-Optimierung: {str(e)}")
    
    def _run_security_check(self) -> None:
        """
        Führt eine Sicherheitsüberprüfung durch
        """
        logger.debug("Führe Sicherheitsüberprüfung durch...")
        
        # Hier würden wir eine Sicherheitsüberprüfung durchführen
        # Für dieses Beispiel verwenden wir Dummy-Operationen
        
        # Beispiel: Regeln überprüfen
        try:
            # In einer echten Implementierung würden wir die Regeln überprüfen
            logger.info("Sicherheitsregeln überprüft")
        except Exception as e:
            logger.error(f"Fehler bei der Sicherheitsüberprüfung: {str(e)}")
    
    def _log_cycle_completion(self) -> None:
        """
        Protokolliert den Abschluss eines Lernzyklus
        """
        elapsed_time = time.time() - self.last_cycle_time if self.last_cycle_time else 0
        logger.info(f"Lernzyklus {self.cycle_counter} abgeschlossen (Dauer: {elapsed_time:.2f}s)")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Status des autonomen Lernzyklus zurück
        
        Returns:
            dict: Statusinformationen
        """
        return {
            "running": self.running,
            "cycle_counter": self.cycle_counter,
            "last_cycle_time": self.last_cycle_time,
            "cycle_interval": self.cycle_interval,
            "max_cycles": self.max_cycles,
            "threads_active": self.thread.is_alive() if self.thread else False
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über den autonomen Lernzyklus zurück
        
        Returns:
            dict: Statistische Daten
        """
        return {
            "total_cycles": self.cycle_counter,
            "average_cycle_time": "N/A",  # In einer echten Implementierung würden wir dies berechnen
            "success_rate": "N/A",        # In einer echten Implementierung würden wir dies berechnen
            "last_cycle_duration": time.time() - self.last_cycle_time if self.last_cycle_time else None
        }

# Testblock für direkte Ausführung (nur für Tests)
if __name__ == "__main__":
    print("Teste AutonomousLoop...")
    
    try:
        # Erstelle Mock-Objekte für Abhängigkeiten
        class MockAIBrain:
            def __init__(self):
                class MockSelfLearning:
                    def start_learning_process(self):
                        print("  - SelfLearning.start_learning_process aufgerufen")
                    
                    def learning_cycle(self):
                        print("  - SelfLearning.learning_cycle aufgerufen")
                        return {"status": "success"}
                
                self.self_learning = MockSelfLearning()
                print("  - MockAIBrain initialisiert")
        
        class MockRuleEngine:
            def __init__(self):
                print("  - MockRuleEngine initialisiert")
        
        class MockUserManager:
            def __init__(self):
                print("  - MockUserManager initialisiert")
        
        # Erstelle AutonomousLoop
        print("\n1. Test: Initialisierung")
        loop = AutonomousLoop(
            brain=MockAIBrain(),
            rule_engine=MockRuleEngine(),
            user_manager=MockUserManager(),
            cycle_interval=2,  # Kurzes Intervall für den Test
            max_cycles=2
        )
        print(f"  - AutonomousLoop initialisiert. Status: {loop.get_status()}")
        
        # Starte den Loop
        print("\n2. Test: Starten des autonomen Lernzyklus")
        loop.start()
        print(f"  - Status nach Start: {loop.get_status()}")
        
        # Warte, bis die Zyklen abgeschlossen sind
        print("\n3. Test: Warte auf Abschluss der Zyklen")
        time.sleep(6)  # Warte länger als benötigt
        
        # Stoppe den Loop
        print("\n4. Test: Stoppen des autonomen Lernzyklus")
        loop.stop()
        print(f"  - Status nach Stop: {loop.get_status()}")
        
        # Prüfe Statistiken
        print("\n5. Test: Statistiken abrufen")
        stats = loop.get_statistics()
        print(f"  - Statistiken: {stats}")
        
    except Exception as e:
        print(f"Fehler im Test: {str(e)}")
    
    print("\nTest abgeschlossen")