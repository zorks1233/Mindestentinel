"""
main.py
Hauptstartskript für Mindestentinel - Die Alpha-Projekt KI AGI Super KI
"""

import os
import sys
import logging
import argparse
import uvicorn
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

# Robuste Projekt-Root-Erkennung
def get_project_root() -> str:
    """
    Findet das Projekt-Root-Verzeichnis unabhängig vom aktuellen Arbeitsverzeichnis
    
    Returns:
        str: Absolute Pfad zum Projekt-Root
    """
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # Versuche 1: Von src aus
    project_root = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Versuche 2: Von Root aus
    project_root = current_dir
    if os.path.exists(os.path.join(project_root, "src", "core")):
        return project_root
    
    # Versuche 3: Projekt-Root ist zwei Ebenen höher
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if os.path.exists(os.path.join(project_root, "core")):
        return project_root
    
    # Fallback: Aktuelles Verzeichnis
    return os.getcwd()

# Setze PYTHONPATH korrekt
PROJECT_ROOT = get_project_root()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import-Handling für ConfigLoader
try:
    from config.config_loader import load_config
    logging.info("ConfigLoader erfolgreich importiert")
except ImportError as e1:
    try:
        # Versuche aus src/config zu importieren
        from src.config.config_loader import load_config
        logging.info("ConfigLoader erfolgreich aus src/config importiert")
    except ImportError as e2:
        try:
            # Dynamischer Importversuch
            config_loader_path = os.path.join(PROJECT_ROOT, "config", "config_loader.py")
            
            if not os.path.exists(config_loader_path):
                config_loader_path = os.path.join(PROJECT_ROOT, "src", "config", "config_loader.py")
            
            if os.path.exists(config_loader_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("config_loader", config_loader_path)
                config_loader_module = importlib.util.module_from_spec(spec)
                sys.modules["config_loader"] = config_loader_module
                spec.loader.exec_module(config_loader_module)
                load_config = config_loader_module.load_config
                logging.info(f"ConfigLoader dynamisch aus {config_loader_path} geladen")
            else:
                raise ImportError(f"config_loader.py nicht gefunden unter: {config_loader_path}")
        except Exception as e3:
            logging.error(f"Alle Importversuche für ConfigLoader fehlgeschlagen: {str(e1)}, {str(e2)}, {str(e3)}")
            # Definiere eine Dummy-Implementierung
            def load_config(config_name: str = "main.yaml") -> Dict[str, Any]:
                logging.warning("ConfigLoader ist eine Dummy-Implementierung - bitte korrigieren")
                return {
                    "system": {
                        "debug": True,
                        "log_level": "INFO",
                        "log_dir": "logs"
                    },
                    "api": {
                        "port": 8000,
                        "host": "0.0.0.0"
                    },
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

# Import-Handling für Core-Module
try:
    from core import TaskManagement, SelfLearning, RuleEngine, ModelManager, UserManager, AIBrain, AuthManager, ProtectionModule
    logging.debug("Core-Module erfolgreich importiert")
except ImportError:
    try:
        from src.core import TaskManagement, SelfLearning, RuleEngine, ModelManager, UserManager, AIBrain, AuthManager, ProtectionModule
        logging.debug("Core-Module erfolgreich aus src/core importiert")
    except ImportError:
        # Fallback: Importiere jedes Modul einzeln mit robustem Handling
        logging.warning("Versuche einzelne Core-Module zu importieren...")
        
        # Import-Handling für jedes Modul (wird bereits in core/__init__.py behandelt)
        from core.task_management import TaskManagement
        from core.self_learning import SelfLearning
        from core.rule_engine import RuleEngine
        from core.model_manager import ModelManager
        from core.user_manager import UserManager
        from core.ai_engine import AIBrain
        from core.auth_manager import AuthManager
        from core.protection_module import ProtectionModule

# Initialisiere Logging
def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> None:
    """
    Konfiguriert das Logging-System
    
    Args:
        log_dir: Verzeichnis für Log-Dateien
        log_level: Logging-Stufe (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Erstelle Log-Verzeichnis, falls nicht vorhanden
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Konfiguriere Logging
    log_file = os.path.join(log_dir, f"mindestentinel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Setze spezifische Log-Level für bestimmte Module
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    
    logging.info(f"Logging konfiguriert. Logs werden gespeichert in: {log_dir}")

def build_components(enable_autonomy: bool = False) -> Tuple[
    AIBrain, 
    ModelManager, 
    'PluginManager', 
    Optional['AutonomousLoop'], 
    UserManager, 
    AuthManager, 
    RuleEngine
]:
    """
    Baut alle Komponenten des Systems auf
    
    Args:
        enable_autonomy: Gibt an, ob autonome Funktionen aktiviert werden sollen
    
    Returns:
        Tuple aller Hauptkomponenten
    """
    logger = logging.getLogger("mindestentinel.main")
    logger.info("Initialisiere ModelManager...")
    
    try:
        # Lade Konfiguration
        config = load_config()
        logger.debug("Konfiguration geladen")
    except Exception as e:
        logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
        raise
    
    try:
        # Initialisiere RuleEngine mit korrektem Pfad
        rules_path = os.path.join(PROJECT_ROOT, "config", "rules.yaml")
        logger.info(f"Verwende Regelpfad: {rules_path}")
        
        rule_engine = RuleEngine(rules_path=rules_path)
        rule_engine.load_rules()
        logger.info("RuleEngine initialisiert.")
        
        if not rule_engine.rules:
            logger.warning("Keine Regeln geladen")
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des RuleEngines: {str(e)}")
        raise
    
    try:
        # Initialisiere ModelManager
        model_manager = ModelManager(config)
        logger.info("ModelManager initialisiert.")
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des ModelManagers: {str(e)}")
        raise
    
    try:
        # Initialisiere PluginManager
        logger.info("Initialisiere PluginManager...")
        from core.plugin_manager import PluginManager
        plugin_manager = PluginManager()
        plugin_manager.load_plugins()
        logger.info(f"PluginManager initialisiert. Plugins geladen: ({len(plugin_manager.plugins)})")
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des PluginManagers: {str(e)}")
        raise
    
    try:
        # Initialisiere UserManager
        user_manager = UserManager()
        logger.debug("UserManager initialisiert.")
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des UserManagers: {str(e)}")
        raise
    
    try:
        # Initialisiere AuthManager
        auth_manager = AuthManager()
        logger.debug("AuthManager initialisiert.")
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des AuthManagers: {str(e)}")
        raise
    
    try:
        # Initialisiere AIBrain mit den korrekten Parametern
        logger.info("Initialisiere AIBrain...")
        brain = AIBrain(
            config=config,
            model_manager=model_manager,
            rule_engine=rule_engine,
            user_manager=user_manager,
            enable_autonomy=enable_autonomy
        )
        logger.info("AIBrain erfolgreich initialisiert")
    except Exception as e:
        logger.error(f"Konnte AIBrain nicht importieren: {str(e)}")
        raise
    
    # Initialisiere AutonomousLoop, wenn erforderlich
    autonomous_loop = None
    if enable_autonomy:
        try:
            logger.info("Initialisiere AutonomousLoop...")
            from core.autonomous_loop import AutonomousLoop
            autonomous_loop = AutonomousLoop(
                brain=brain,
                rule_engine=rule_engine,
                user_manager=user_manager
            )
            logger.info("AutonomousLoop initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung des AutonomousLoops: {str(e)}")
    
    return brain, model_manager, plugin_manager, autonomous_loop, user_manager, auth_manager, rule_engine

def main():
    """Hauptfunktion des Programms"""
    logger = logging.getLogger("mindestentinel.main")
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Mindestentinel - Die Alpha-Projekt KI AGI Super KI")
    parser.add_argument("--start-rest", action="store_true", help="Starte den REST-API-Server")
    parser.add_argument("--enable-autonomy", action="store_true", help="Aktiviere autonome Funktionen")
    parser.add_argument("--api-port", type=int, default=8000, help="API-Port (Standard: 8000)")
    parser.add_argument("--api-host", type=str, default="0.0.0.0", help="API-Host (Standard: 0.0.0.0)")
    args = parser.parse_args()
    
    try:
        # Lade Konfiguration für Logging
        try:
            config = load_config()
            log_dir = config.get("system", {}).get("log_dir", "logs")
            log_level = config.get("system", {}).get("log_level", "INFO")
        except:
            log_dir = "logs"
            log_level = "INFO"
        
        # Setze Logging auf
        setup_logging(log_dir=log_dir, log_level=log_level)
        logger.info("Logging konfiguriert.")
        
        # Baue Komponenten auf
        logger.info("Baue Systemkomponenten auf...")
        brain, model_manager, plugin_manager, autonomous_loop, user_manager, auth_manager, rule_engine = build_components(
            enable_autonomy=args.enable_autonomy
        )
        
        # Starte die KI
        logger.info("Starte AIBrain...")
        brain.start()
        
        # Starte autonomen Loop, wenn aktiviert
        if autonomous_loop:
            logger.info("Starte autonomen Loop...")
            autonomous_loop.start()
        
        # Starte REST-API, wenn gewünscht
        if args.start_rest:
            logger.info(f"Starte REST-API auf {args.api_host}:{args.api_port}...")
            try:
                from api.rest_api import app
                uvicorn.run(
                    app, 
                    host=args.api_host, 
                    port=args.api_port,
                    log_level="warning"
                )
            except Exception as e:
                logger.error(f"Fehler beim Starten der REST-API: {str(e)}")
                raise
        
        # Warte auf Benutzerabbruch, wenn REST-API läuft
        if args.start_rest:
            try:
                logger.info("Drücken Sie STRG+C zum Beenden...")
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Benutzerabbruch erkannt. Beende...")
        
    except Exception as e:
        logger.exception(f"Kritischer Fehler im Hauptprogramm: {str(e)}")
        raise
    finally:
        # System herunterfahren
        logger.info("System shutdown complete.")

if __name__ == "__main__":
    # Patch für Multiprocessing unter Windows
    try:
        import multiprocessing
        multiprocessing.set_start_method('spawn')
        print("Multiprocessing-Patch erfolgreich geladen")
    except Exception as e:
        print(f"Multiprocessing-Patch fehlgeschlagen: {str(e)}")
    
    # Starte das Hauptprogramm
    main()