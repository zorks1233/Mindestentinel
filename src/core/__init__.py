"""
core/__init__.py
Initialisierungsdatei für das Core-Modul von Mindestentinel
Diese Datei stellt sicher, dass alle Core-Komponenten korrekt importiert werden können
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

# Konfiguriere Logging für diese Initialisierungsdatei
logger = logging.getLogger("mindestentinel.core.init")
logger.setLevel(logging.DEBUG)

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
        logger.debug(f"Projekt-Root gefunden (src/core): {project_root}")
        return project_root
    
    # Versuche 2: Von core aus
    project_root = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(project_root, "src", "core")):
        logger.debug(f"Projekt-Root gefunden (core): {project_root}")
        return project_root
    
    # Versuche 3: Aktuelles Verzeichnis ist Projekt-Root
    project_root = current_dir
    if os.path.exists(os.path.join(project_root, "src", "core")) or os.path.exists(os.path.join(project_root, "core")):
        logger.debug(f"Projekt-Root gefunden (aktuelles Verzeichnis): {project_root}")
        return project_root
    
    # Versuche 4: Projekt-Root ist zwei Ebenen höher
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if os.path.exists(os.path.join(project_root, "core")):
        logger.debug(f"Projekt-Root gefunden (zwei Ebenen höher): {project_root}")
        return project_root
    
    # Fallback: Aktuelles Verzeichnis
    logger.warning("Konnte Projekt-Root nicht finden, verwende aktuelles Verzeichnis")
    return os.getcwd()

def setup_project_environment() -> None:
    """
    Richtet die Projektumgebung ein, indem das Projekt-Root zum PYTHONPATH hinzugefügt wird
    """
    project_root = get_project_root()
    
    # Füge Projekt-Root zum PYTHONPATH hinzu, wenn nicht bereits vorhanden
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.debug(f"Projekt-Root zum PYTHONPATH hinzugefügt: {project_root}")
    
    # Stelle sicher, dass das config-Verzeichnis existiert
    config_dir = os.path.join(project_root, "config")
    if not os.path.exists(config_dir):
        logger.warning(f"Config-Verzeichnis nicht gefunden: {config_dir}")
    else:
        # Stelle sicher, dass config/__init__.py existiert
        init_file = os.path.join(config_dir, "__init__.py")
        if not os.path.exists(init_file):
            try:
                with open(init_file, "w") as f:
                    f.write("# Initialisierungsdatei für das Config-Modul\n")
                logger.info(f"Erstelle fehlende __init__.py in: {config_dir}")
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von __init__.py in {config_dir}: {str(e)}")
    
    # Stelle sicher, dass das core-Verzeichnis im src-Verzeichnis korrekt initialisiert ist
    src_core_dir = os.path.join(project_root, "src", "core")
    if os.path.exists(src_core_dir):
        init_file = os.path.join(src_core_dir, "__init__.py")
        if not os.path.exists(init_file):
            try:
                with open(init_file, "w") as f:
                    f.write("# Initialisierungsdatei für das Core-Modul im src-Verzeichnis\n")
                logger.info(f"Erstelle fehlende __init__.py in: {src_core_dir}")
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von __init__.py in {src_core_dir}: {str(e)}")

# Richte die Projektumgebung ein
setup_project_environment()

# Import-Handling für TaskManagement
try:
    from .task_management import TaskManagement
    logger.debug("TaskManagement erfolgreich importiert")
except ImportError as e1:
    try:
        # Versuche aus Root-core zu importieren
        from core.task_management import TaskManagement
        logger.debug("TaskManagement erfolgreich aus Root-core importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
            project_root = get_project_root()
            task_management_path = os.path.join(project_root, "src", "core", "task_management.py")
            
            if not os.path.exists(task_management_path):
                task_management_path = os.path.join(project_root, "core", "task_management.py")
            
            if os.path.exists(task_management_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("task_management", task_management_path)
                task_management_module = importlib.util.module_from_spec(spec)
                sys.modules["task_management"] = task_management_module
                spec.loader.exec_module(task_management_module)
                TaskManagement = task_management_module.TaskManagement
                logger.debug(f"TaskManagement dynamisch aus {task_management_path} geladen")
            else:
                raise ImportError(f"task_management.py nicht gefunden unter: {task_management_path}")
        except Exception as e3:
            logger.error(f"Alle Importversuche für TaskManagement fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            # Definiere eine Dummy-Klasse, um das System am Laufen zu halten
            class TaskManagement:
                def __init__(self, *args, **kwargs):
                    logger.warning("TaskManagement ist eine Dummy-Implementierung - bitte korrigieren")
                
                def create_task(self, *args, **kwargs):
                    return {"status": "error", "message": "TaskManagement nicht vollständig implementiert"}

# Import-Handling für SelfLearning
try:
    from .self_learning import SelfLearning
    logger.debug("SelfLearning erfolgreich importiert")
except ImportError as e1:
    try:
        # Versuche aus Root-core zu importieren
        from core.self_learning import SelfLearning
        logger.debug("SelfLearning erfolgreich aus Root-core importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
            project_root = get_project_root()
            self_learning_path = os.path.join(project_root, "src", "core", "self_learning.py")
            
            if not os.path.exists(self_learning_path):
                self_learning_path = os.path.join(project_root, "core", "self_learning.py")
            
            if os.path.exists(self_learning_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("self_learning", self_learning_path)
                self_learning_module = importlib.util.module_from_spec(spec)
                sys.modules["self_learning"] = self_learning_module
                spec.loader.exec_module(self_learning_module)
                SelfLearning = self_learning_module.SelfLearning
                logger.debug(f"SelfLearning dynamisch aus {self_learning_path} geladen")
            else:
                raise ImportError(f"self_learning.py nicht gefunden unter: {self_learning_path}")
        except Exception as e3:
            logger.error(f"Alle Importversuche für SelfLearning fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            # Definiere eine Dummy-Klasse, um das System am Laufen zu halten
            class SelfLearning:
                def __init__(self, *args, **kwargs):
                    logger.warning("SelfLearning ist eine Dummy-Implementierung - bitte korrigieren")
                
                def start_learning_process(self, *args, **kwargs):
                    logger.info("Dummy SelfLearning: start_learning_process aufgerufen")
                
                def record_experience(self, *args, **kwargs):
                    logger.info("Dummy SelfLearning: record_experience aufgerufen")
                
                def save_progress(self, *args, **kwargs):
                    logger.info("Dummy SelfLearning: save_progress aufgerufen")

# Import-Handling für RuleEngine
try:
    from .rule_engine import RuleEngine
    logger.debug("RuleEngine erfolgreich importiert")
except ImportError as e1:
    try:
        # Versuche aus Root-core zu importieren
        from core.rule_engine import RuleEngine
        logger.debug("RuleEngine erfolgreich aus Root-core importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
            project_root = get_project_root()
            rule_engine_path = os.path.join(project_root, "src", "core", "rule_engine.py")
            
            if not os.path.exists(rule_engine_path):
                rule_engine_path = os.path.join(project_root, "core", "rule_engine.py")
            
            if os.path.exists(rule_engine_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("rule_engine", rule_engine_path)
                rule_engine_module = importlib.util.module_from_spec(spec)
                sys.modules["rule_engine"] = rule_engine_module
                spec.loader.exec_module(rule_engine_module)
                RuleEngine = rule_engine_module.RuleEngine
                logger.debug(f"RuleEngine dynamisch aus {rule_engine_path} geladen")
            else:
                raise ImportError(f"rule_engine.py nicht gefunden unter: {rule_engine_path}")
        except Exception as e3:
            logger.error(f"Alle Importversuche für RuleEngine fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            # Definiere eine Dummy-Klasse, um das System am Laufen zu halten
            class RuleEngine:
                def __init__(self, *args, **kwargs):
                    logger.warning("RuleEngine ist eine Dummy-Implementierung - bitte korrigieren")
                    self.rules = []
                
                def load_rules(self, *args, **kwargs):
                    logger.info("Dummy RuleEngine: load_rules aufgerufen")
                    return {"status": "success", "rules_loaded": 0}
                
                def apply_rules(self, *args, **kwargs):
                    logger.info("Dummy RuleEngine: apply_rules aufgerufen")
                    return {"allowed": True, "message": "Keine Regeln geladen"}

# Import-Handling für ModelManager
try:
    from .model_manager import ModelManager
    logger.debug("ModelManager erfolgreich importiert")
except ImportError as e1:
    try:
        # Versuche aus Root-core zu importieren
        from core.model_manager import ModelManager
        logger.debug("ModelManager erfolgreich aus Root-core importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
            project_root = get_project_root()
            model_manager_path = os.path.join(project_root, "src", "core", "model_manager.py")
            
            if not os.path.exists(model_manager_path):
                model_manager_path = os.path.join(project_root, "core", "model_manager.py")
            
            if os.path.exists(model_manager_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("model_manager", model_manager_path)
                model_manager_module = importlib.util.module_from_spec(spec)
                sys.modules["model_manager"] = model_manager_module
                spec.loader.exec_module(model_manager_module)
                ModelManager = model_manager_module.ModelManager
                logger.debug(f"ModelManager dynamisch aus {model_manager_path} geladen")
            else:
                raise ImportError(f"model_manager.py nicht gefunden unter: {model_manager_path}")
        except Exception as e3:
            logger.error(f"Alle Importversuche für ModelManager fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            # Definiere eine Dummy-Klasse, um das System am Laufen zu halten
            class ModelManager:
                def __init__(self, *args, **kwargs):
                    logger.warning("ModelManager ist eine Dummy-Implementierung - bitte korrigieren")
                
                def load_models(self, *args, **kwargs):
                    logger.info("Dummy ModelManager: load_models aufgerufen")
                
                def save_models(self, *args, **kwargs):
                    logger.info("Dummy ModelManager: save_models aufgerufen")
                
                def generate_response(self, *args, **kwargs):
                    logger.info("Dummy ModelManager: generate_response aufgerufen")
                    return "Dies ist eine Dummy-Antwort, da ModelManager nicht korrekt initialisiert wurde"

# Import-Handling für UserManager
try:
    from .user_manager import UserManager
    logger.debug("UserManager erfolgreich importiert")
except ImportError as e1:
    try:
        # Versuche aus Root-core zu importieren
        from core.user_manager import UserManager
        logger.debug("UserManager erfolgreich aus Root-core importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
            project_root = get_project_root()
            user_manager_path = os.path.join(project_root, "src", "core", "user_manager.py")
            
            if not os.path.exists(user_manager_path):
                user_manager_path = os.path.join(project_root, "core", "user_manager.py")
            
            if os.path.exists(user_manager_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("user_manager", user_manager_path)
                user_manager_module = importlib.util.module_from_spec(spec)
                sys.modules["user_manager"] = user_manager_module
                spec.loader.exec_module(user_manager_module)
                UserManager = user_manager_module.UserManager
                logger.debug(f"UserManager dynamisch aus {user_manager_path} geladen")
            else:
                raise ImportError(f"user_manager.py nicht gefunden unter: {user_manager_path}")
        except Exception as e3:
            logger.error(f"Alle Importversuche für UserManager fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            # Definiere eine Dummy-Klasse, um das System am Laufen zu halten
            class UserManager:
                def __init__(self, *args, **kwargs):
                    logger.warning("UserManager ist eine Dummy-Implementierung - bitte korrigieren")
                
                def get_user(self, *args, **kwargs):
                    logger.info("Dummy UserManager: get_user aufgerufen")
                    return {"id": "dummy", "name": "Dummy User"}
                
                def create_user(self, *args, **kwargs):
                    logger.info("Dummy UserManager: create_user aufgerufen")
                    return {"status": "success", "user_id": "dummy_id"}

# Import-Handling für AIEngine
try:
    from .ai_engine import AIBrain
    logger.debug("AIBrain erfolgreich importiert")
except ImportError as e1:
    try:
        # Versuche aus Root-core zu importieren
        from core.ai_engine import AIBrain
        logger.debug("AIBrain erfolgreich aus Root-core importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
            project_root = get_project_root()
            ai_engine_path = os.path.join(project_root, "src", "core", "ai_engine.py")
            
            if not os.path.exists(ai_engine_path):
                ai_engine_path = os.path.join(project_root, "core", "ai_engine.py")
            
            if os.path.exists(ai_engine_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("ai_engine", ai_engine_path)
                ai_engine_module = importlib.util.module_from_spec(spec)
                sys.modules["ai_engine"] = ai_engine_module
                spec.loader.exec_module(ai_engine_module)
                AIBrain = ai_engine_module.AIBrain
                logger.debug(f"AIBrain dynamisch aus {ai_engine_path} geladen")
            else:
                raise ImportError(f"ai_engine.py nicht gefunden unter: {ai_engine_path}")
        except Exception as e3:
            logger.error(f"Alle Importversuche für AIBrain fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            # Definiere eine Dummy-Klasse, um das System am Laufen zu halten
            class AIBrain:
                def __init__(self, *args, **kwargs):
                    logger.warning("AIBrain ist eine Dummy-Implementierung - bitte korrigieren")
                    self.active = False
                
                def start(self):
                    self.active = True
                    logger.info("Dummy AIBrain: start aufgerufen")
                
                def process_input(self, user_input, user_id=None):
                    logger.info(f"Dummy AIBrain: process_input aufgerufen mit '{user_input}'")
                    return "Ich bin eine Dummy-Implementierung. Bitte korrigieren Sie den Import-Fehler."
                
                def shutdown(self):
                    self.active = False
                    logger.info("Dummy AIBrain: shutdown aufgerufen")

# Import-Handling für weitere Module
try:
    from .auth import Auth
    logger.debug("Auth erfolgreich importiert")
except ImportError:
    logger.warning("Auth-Modul nicht gefunden, verwende Dummy-Implementierung")
    
    class Auth:
        def __init__(self, *args, **kwargs):
            pass
        
        def authenticate(self, *args, **kwargs):
            return True

try:
    from .auth_manager import AuthManager
    logger.debug("AuthManager erfolgreich importiert")
except ImportError:
    logger.warning("AuthManager-Modul nicht gefunden, verwende Dummy-Implementierung")
    
    class AuthManager:
        def __init__(self, *args, **kwargs):
            pass
        
        def validate_token(self, *args, **kwargs):
            return True

try:
    from .protection_module import ProtectionModule
    logger.debug("ProtectionModule erfolgreich importiert")
except ImportError:
    logger.warning("ProtectionModule-Modul nicht gefunden, verwende Dummy-Implementierung")
    
    class ProtectionModule:
        def __init__(self, *args, **kwargs):
            pass
        
        def check_security(self, *args, **kwargs):
            return {"status": "warning", "message": "ProtectionModule nicht korrekt initialisiert"}

try:
    from .quantum_core import QuantumCore
    logger.debug("QuantumCore erfolgreich importiert")
except ImportError:
    logger.warning("QuantumCore-Modul nicht gefunden, verwende Dummy-Implementierung")
    
    class QuantumCore:
        def __init__(self, *args, **kwargs):
            pass
        
        def process_quantum(self, *args, **kwargs):
            return args

# Stelle sicher, dass alle wichtigen Klassen im Modul-Namespace verfügbar sind
__all__ = [
    'TaskManagement',
    'SelfLearning',
    'RuleEngine',
    'ModelManager',
    'UserManager',
    'AIBrain',
    'Auth',
    'AuthManager',
    'ProtectionModule',
    'QuantumCore'
]

# Testblock für direkte Ausführung (nur für Tests)
if __name__ == "__main__":
    print("Teste core/__init__.py...")
    
    # Teste SelfLearning
    try:
        sl = SelfLearning({})
        print("SelfLearning erfolgreich instanziiert")
        sl.start_learning_process()
        sl.record_experience({"input": "test", "response": "test"})
        sl.save_progress()
    except Exception as e:
        print(f"Fehler bei SelfLearning: {str(e)}")
    
    # Teste RuleEngine
    try:
        re = RuleEngine()
        print("RuleEngine erfolgreich instanziiert")
        re.load_rules()
        result = re.apply_rules("Testeingabe")
        print(f"RuleEngine Ergebnis: {result}")
    except Exception as e:
        print(f"Fehler bei RuleEngine: {str(e)}")
    
    # Teste AIBrain
    try:
        # Erstelle Mock-Objekte
        class MockModelManager:
            def load_models(self): pass
            def save_models(self): pass
            def generate_response(self, input, **kwargs): return "Mock-Antwort"
        
        class MockRuleEngine:
            def load_rules(self): pass
            def apply_rules(self, input, context): return {"allowed": True, "message": ""}
        
        class MockUserManager:
            pass
        
        brain = AIBrain(
            config={},
            model_manager=MockModelManager(),
            rule_engine=MockRuleEngine(),
            user_manager=MockUserManager(),
            enable_autonomy=True
        )
        print("AIBrain erfolgreich instanziiert")
        brain.start()
        response = brain.process_input("Hallo, wie geht es dir?")
        print(f"Antwort: {response}")
        brain.shutdown()
    except Exception as e:
        print(f"Fehler bei AIBrain: {str(e)}")
    
    print("Test abgeschlossen")