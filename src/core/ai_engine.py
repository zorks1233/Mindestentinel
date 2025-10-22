"""
ai_engine.py
Hauptmodul für die KI-Engine von Mindestentinel
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Robuste Projekt-Root-Erkennung
def get_project_root() -> str:
    """Findet das Projekt-Root-Verzeichnis unabhängig vom Ausführungspfad"""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # Versuche 1: Von core-Verzeichnis aus
    project_root = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(project_root, "src", "core")):
        return project_root
    
    # Versuche 2: Von src/core-Verzeichnis aus
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 3: Projekt-Root ist zwei Ebenen höher
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Fallback: Aktuelles Verzeichnis
    return os.getcwd()

# Setze PYTHONPATH korrekt
PROJECT_ROOT = get_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    logging.debug(f"PROJECT_ROOT zu PYTHONPATH hinzugefügt: {PROJECT_ROOT}")

# Import-Handling für SelfLearning
try:
    # Versuche 1: Import aus src/core
    from src.core.self_learning import SelfLearning
    logging.debug("SelfLearning erfolgreich von src.core.self_learning importiert")
except ImportError as e1:
    try:
        # Versuche 2: Import aus core (wenn von Root gestartet)
        from self_learning import SelfLearning
        logging.debug("SelfLearning erfolgreich von core.self_learning importiert")
    except ImportError as e2:
        try:
            # Versuche 3: Import relativ zum Projekt-Root
            sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
            from core.self_learning import SelfLearning
            logging.debug("SelfLearning erfolgreich von src.core.self_learning (relativ) importiert")
        except ImportError as e3:
            # Versuche 4: Direkter Import über dynamischen Pfad
            try:
                self_learning_path = os.path.join(PROJECT_ROOT, "src", "core", "self_learning.py")
                if not os.path.exists(self_learning_path):
                    self_learning_path = os.path.join(PROJECT_ROOT, "core", "self_learning.py")
                
                if os.path.exists(self_learning_path):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("self_learning", self_learning_path)
                    self_learning_module = importlib.util.module_from_spec(spec)
                    sys.modules["self_learning"] = self_learning_module
                    spec.loader.exec_module(self_learning_module)
                    SelfLearning = self_learning_module.SelfLearning
                    logging.debug(f"SelfLearning dynamisch aus {self_learning_path} geladen")
                else:
                    raise ImportError(f"self_learning.py nicht gefunden unter: {self_learning_path}")
            except Exception as e4:
                logging.error(f"Alle Importversuche für SelfLearning fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}, {str(e4)}")
                raise

# Import weiterer benötigter Module
try:
    from src.core.rule_engine import RuleEngine
    logging.debug("RuleEngine erfolgreich von src.core.rule_engine importiert")
except ImportError:
    try:
        from rule_engine import RuleEngine
        logging.debug("RuleEngine erfolgreich von core.rule_engine importiert")
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
            from core.rule_engine import RuleEngine
            logging.debug("RuleEngine erfolgreich von src.core.rule_engine (relativ) importiert")
        except ImportError:
            logging.error("Konnte RuleEngine nicht importieren")
            raise

try:
    from src.core.model_manager import ModelManager
    logging.debug("ModelManager erfolgreich von src.core.model_manager importiert")
except ImportError:
    try:
        from model_manager import ModelManager
        logging.debug("ModelManager erfolgreich von core.model_manager importiert")
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
            from core.model_manager import ModelManager
            logging.debug("ModelManager erfolgreich von src.core.model_manager (relativ) importiert")
        except ImportError:
            logging.error("Konnte ModelManager nicht importieren")
            raise

try:
    from src.core.user_manager import UserManager
    logging.debug("UserManager erfolgreich von src.core.user_manager importiert")
except ImportError:
    try:
        from user_manager import UserManager
        logging.debug("UserManager erfolgreich von core.user_manager importiert")
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))
            from core.user_manager import UserManager
            logging.debug("UserManager erfolgreich von src.core.user_manager (relativ) importiert")
        except ImportError:
            logging.error("Konnte UserManager nicht importieren")
            raise

# Initialisiere Logging
logger = logging.getLogger("mindestentinel.ai_engine")
logger.setLevel(logging.INFO)

class AIBrain:
    """
    Hauptklasse für die KI-Intelligenz von Mindestentinel
    Koordiniert alle Komponenten der KI und ermöglicht autonome Operationen
    """
    
    def __init__(self, config: Dict[str, Any], model_manager: ModelManager, 
                 rule_engine: RuleEngine, user_manager: UserManager, 
                 enable_autonomy: bool = False):
        """
        Initialisiert die AIBrain-Komponente
        
        Args:
            config: Konfigurationsdaten für die KI
            model_manager: Instanz des ModelManagers
            rule_engine: Instanz des RuleEngines
            user_manager: Instanz des UserManagers
            enable_autonomy: Gibt an, ob autonome Funktionen aktiviert sind
        """
        self.config = config
        self.model_manager = model_manager
        self.rule_engine = rule_engine
        self.user_manager = user_manager
        self.enable_autonomy = enable_autonomy
        self.self_learning = None
        self.active = False
        self.last_thought = None
        self.thought_history = []
        
        # Initialisiere SelfLearning
        try:
            self.self_learning = SelfLearning(config.get("self_learning", {}))
            logger.info("SelfLearning-Modul erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung von SelfLearning: {str(e)}")
            raise
        
        logger.info("AIBrain erfolgreich initialisiert")
    
    def start(self):
        """Startet die KI-Engine und alle zugehörigen Komponenten"""
        logger.info("Starte AIBrain...")
        self.active = True
        
        # Initialisiere grundlegende Systemkomponenten
        self.model_manager.load_models()
        self.rule_engine.load_rules()
        
        # Starte autonome Prozesse, wenn aktiviert
        if self.enable_autonomy:
            logger.info("Autonome Funktionen werden aktiviert")
            self._start_autonomous_processes()
        else:
            logger.info("Autonome Funktionen sind deaktiviert")
    
    def _start_autonomous_processes(self):
        """Startet alle autonomen Prozesse der KI"""
        logger.info("Starte autonome Prozesse...")
        
        # Starte Selbstlernprozess
        if self.self_learning:
            try:
                self.self_learning.start_learning_process()
                logger.info("Selbstlernprozess gestartet")
            except Exception as e:
                logger.error(f"Fehler beim Starten des Selbstlernprozesses: {str(e)}")
        
        # Hier können weitere autonome Prozesse hinzugefügt werden
    
    def process_input(self, user_input: str, user_id: str = None) -> str:
        """
        Verarbeitet Benutzereingaben und generiert eine Antwort
        
        Args:
            user_input: Die Eingabe des Benutzers
            user_id: Optional die ID des Benutzers für personalisierte Antworten
            
        Returns:
            Die generierte Antwort der KI
        """
        if not self.active:
            logger.warning("Versuch, AIBrain zu verwenden, während sie nicht aktiv ist")
            return "System ist nicht aktiv. Bitte starten Sie zuerst die KI."
        
        logger.debug(f"Verarbeite Eingabe von Benutzer {user_id}: {user_input}")
        
        # Speichere den aktuellen Gedanken
        self.last_thought = {
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "user_id": user_id
        }
        self.thought_history.append(self.last_thought)
        
        # Wende Regeln an
        try:
            rules_result = self.rule_engine.apply_rules(user_input, context={
                "user_id": user_id,
                "user_input": user_input
            })
            if not rules_result["allowed"]:
                logger.warning(f"Eingabe verletzt Regeln: {rules_result['message']}")
                return rules_result["message"]
        except Exception as e:
            logger.error(f"Fehler bei der Regelanwendung: {str(e)}")
        
        # Generiere Antwort basierend auf dem Modell
        try:
            response = self.model_manager.generate_response(
                user_input, 
                user_id=user_id,
                enable_autonomy=self.enable_autonomy
            )
            logger.debug(f"Generierte Antwort: {response}")
            
            # Speichere Lernerfahrungen
            if self.self_learning:
                try:
                    self.self_learning.record_experience({
                        "input": user_input,
                        "response": response,
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Fehler beim Aufzeichnen der Erfahrung: {str(e)}")
            
            return response
        except Exception as e:
            logger.error(f"Fehler bei der Antwortgenerierung: {str(e)}")
            return "Entschuldigung, ich konnte Ihre Anfrage nicht verarbeiten."
    
    def shutdown(self):
        """Fährt die KI-Engine herunter und speichert den Zustand"""
        logger.info("Fahre AIBrain herunter...")
        self.active = False
        
        # Speichere Lernfortschritt
        if self.self_learning:
            try:
                self.self_learning.save_progress()
                logger.info("Lernfortschritt gespeichert")
            except Exception as e:
                logger.error(f"Fehler beim Speichern des Lernfortschritts: {str(e)}")
        
        # Speichere Modellzustände
        self.model_manager.save_models()
        logger.info("AIBrain erfolgreich heruntergefahren")

# Für Tests und direkte Ausführung
if __name__ == "__main__":
    # Beispielkonfiguration
    example_config = {
        "model": {
            "default": "gpt-3.5-turbo",
            "max_tokens": 500
        },
        "self_learning": {
            "enabled": True,
            "learning_rate": 0.01,
            "memory_size": 1000
        }
    }
    
    # Erstelle Mock-Objekte für Abhängigkeiten
    class MockModelManager:
        def load_models(self):
            print("Mock: Modelle geladen")
        def save_models(self):
            print("Mock: Modelle gespeichert")
        def generate_response(self, input, **kwargs):
            return f"Mock-Antwort auf: {input}"
    
    class MockRuleEngine:
        def load_rules(self):
            print("Mock: Regeln geladen")
        def apply_rules(self, input, context):
            return {"allowed": True, "message": ""}
    
    class MockUserManager:
        pass
    
    # Initialisiere und teste AIBrain
    brain = AIBrain(
        config=example_config,
        model_manager=MockModelManager(),
        rule_engine=MockRuleEngine(),
        user_manager=MockUserManager(),
        enable_autonomy=True
    )
    
    brain.start()
    response = brain.process_input("Hallo, wie geht es dir?")
    print(f"Antwort: {response}")
    brain.shutdown()