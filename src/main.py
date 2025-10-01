# src/main.py
"""
Einstiegspunkt für Mindestentinel.
- Startet AIBrain, ModelManager, PluginManager
- CLI-Flags:
    --start-rest      : startet FastAPI REST API (uvicorn)
    --start-ws        : startet WebSocket API
    --enable-autonomy : aktiviert den autonomen Lernzyklus
    --no-start        : nur initialisiert (useful for interactive use)
    --api-host / --api-port
Beispiel:
    python -m src.main --start-rest --enable-autonomy --api-port 8000
"""

import warnings
# Unterdrücke pkg_resources-Warning
warnings.filterwarnings("ignore", category=UserWarning, message="pkg_resources is deprecated")

import argparse
import multiprocessing
import platform
import os
import logging
import uvicorn
import threading
import time
import sys
from typing import Optional, Tuple, List

# Setze PYTHONPATH automatisch auf das Projekt-Root, falls nicht gesetzt
if "PYTHONPATH" not in os.environ:
    # Bestimme das Projekt-Root (angenommen, dass src/ im Projekt-Root liegt)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["PYTHONPATH"] = project_root
    sys.path.insert(0, project_root)
    logging.info(f"PYTHONPATH automatisch gesetzt auf: {project_root}")

# Import des AutonomousLoop Moduls
try:
    from src.core.autonomous_loop import AutonomousLoop
    AUTONOMY_AVAILABLE = True
except ImportError as e:
    logging.warning(f"AutonomousLoop konnte nicht importiert werden: {str(e)}")
    AUTONOMY_AVAILABLE = False

from src.core.model_manager import ModelManager
from src.modules.plugin_manager import PluginManager
from src.core.ai_engine import AIBrain
from src.core.knowledge_base import KnowledgeBase
from src.core.multi_model_orchestrator import MultiModelOrchestrator
from src.core.rule_engine import RuleEngine
from src.core.protection_module import ProtectionModule
from src.core.system_monitor import SystemMonitor
from src.core.model_cloner import ModelCloner
from src.core.knowledge_transfer import KnowledgeTransfer
from src.core.model_trainer import ModelTrainer
from src.core.auth_manager import AuthManager
from src.core.user_manager import UserManager
from src.api.rest_api import create_app
from src.api.websocket_api import create_ws_app
from src.config import setup_logging

# Setze Logging vor allen anderen Initialisierungen
setup_logging()
_LOG = logging.getLogger("mindestentinel.main")

def handle_admin_commands():
    """Verarbeitet Admin-Befehle direkt."""
    # Prüfe, ob es ein Admin-Befehl ist
    if len(sys.argv) > 1 and sys.argv[1] == "admin":
        # Entferne das erste Argument (main.py)
        script_name = sys.argv[0]
        args = sys.argv[2:]  # Überspringe "admin"
        
        # Prüfe, ob es ein Benutzer-Befehl ist
        if len(args) > 0 and args[0] == "users":
            # Entferne "users"
            args = args[1:]
            
            # Bestimme das Skript-Verzeichnis
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            
            # Stelle sicher, dass PYTHONPATH gesetzt ist
            if "PYTHONPATH" not in os.environ:
                os.environ["PYTHONPATH"] = project_root
                sys.path.insert(0, project_root)
            
            # Importiere das Benutzermanagement-Skript
            try:
                from admin_console.commands.manage_users import main as users_main
                
                # Speichere das aktuelle sys.argv
                original_argv = sys.argv
                
                try:
                    # Setze sys.argv auf das Skript-Name + args
                    sys.argv = [script_name] + args
                    
                    # Rufe main ohne Argumente auf (da sie keine Argumente erwartet)
                    users_main()
                    
                    return True
                finally:
                    # Stelle das ursprüngliche sys.argv wieder her
                    sys.argv = original_argv
            except ImportError as e:
                _LOG.error(f"Fehler beim Importieren von manage_users.py: {str(e)}")
                return False
    
    return False

def get_absolute_db_path():
    """Gibt den absoluten Pfad zur Wissensdatenbank zurück."""
    # Bestimme das Projekt-Root absolut
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "data", "knowledge", "knowledge.db")

def build_components(rules_path: Optional[str] = None, enable_autonomy: bool = False) -> Tuple[AIBrain, ModelManager, PluginManager, Optional['AutonomousLoop'], UserManager, AuthManager]:
    """
    Initialisiert alle Systemkomponenten
    
    Args:
        rules_path: Pfad zur Regelkonfiguration
        enable_autonomy: Gibt an, ob der autonome Lernzyklus benötigt wird
        
    Returns:
        Tupel mit (brain, model_manager, plugin_manager, autonomous_loop, user_manager, auth_manager)
        Der letzte Wert ist None, wenn enable_autonomy=False oder nicht verfügbar
    """
    _LOG.info("Initialisiere ModelManager...")
    mm = ModelManager()
    
    _LOG.info("Initialisiere PluginManager...")
    pm = PluginManager()
    
    # Initialisiere die RuleEngine ZUERST, da sie von mehreren Komponenten benötigt wird
    _LOG.info("Initialisiere RuleEngine...")
    rule_engine = RuleEngine(rules_path or os.path.join("config", "rules.yaml"))
    
    # Initialisiere das AIBrain mit der Regelkonfiguration
    _LOG.info("Initialisiere AIBrain...")
    brain = AIBrain(rules_path or os.path.join("config", "rules.yaml"))
    
    # inject model manager
    brain.inject_model_manager(mm)
    
    # Bestimme den absoluten Datenbankpfad
    db_path = get_absolute_db_path()
    
    # Stelle sicher, dass das Verzeichnis existiert
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialisiere die KnowledgeBase mit absolutem Pfad
    if not hasattr(brain, 'knowledge_base') or brain.knowledge_base is None:
        _LOG.info(f"knowledge_base nicht in AIBrain gefunden - initialisiere neu mit Pfad: {db_path}")
        brain.knowledge_base = KnowledgeBase(db_path=db_path)
    
    # Initialisiere den UserManager mit der KnowledgeBase
    _LOG.info("Initialisiere UserManager...")
    user_manager = UserManager(brain.knowledge_base)
    
    # Initialisiere den AuthManager mit der KnowledgeBase
    _LOG.info("Initialisiere AuthManager...")
    auth_manager = AuthManager(brain.knowledge_base, user_manager)
    
    # Stelle sicher, dass mindestens ein Admin-Benutzer existiert
    try:
        # Versuche, den Admin-Benutzer zu erstellen
        if not user_manager.user_exists("admin"):
            from src.core.passwords import is_strong_password
            
            # Prüfe, ob das Passwort stark genug ist
            password = "admin123"
            if isinstance(is_strong_password(password), str):
                _LOG.warning(f"Standard-Passwort ist nicht stark genug: {is_strong_password(password)}")
                # Generiere ein sicheres Passwort
                password = secrets.token_urlsafe(12)
                _LOG.info(f"Generiertes sicheres Passwort für Admin: {password}")
            
            user_manager.create_user("admin", password, is_admin=True)
            _LOG.info("Standard-Admin-Benutzer 'admin' erstellt")
        else:
            _LOG.info("Standard-Admin-Benutzer 'admin' existiert bereits")
    except ValueError:
        _LOG.info("Standard-Admin-Benutzer 'admin' existiert bereits")
    except Exception as e:
        _LOG.error(f"Fehler beim Erstellen des Admin-Benutzers: {str(e)}", exc_info=True)
    
    if not hasattr(brain, 'model_orchestrator') or brain.model_orchestrator is None:
        _LOG.info("model_orchestrator nicht in AIBrain gefunden - initialisiere neu")
        brain.model_orchestrator = MultiModelOrchestrator()
        # WICHTIG: Injiziere den model_manager auch in den neu erstellten Orchestrator
        brain.model_orchestrator.inject_model_manager(mm)
    
    if not hasattr(brain, 'rule_engine') or brain.rule_engine is None:
        _LOG.info("rule_engine nicht in AIBrain gefunden - verwende vorinitialisierte Instanz")
        brain.rule_engine = rule_engine
    
    if not hasattr(brain, 'protection_module') or brain.protection_module is None:
        _LOG.info("protection_module nicht in AIBrain gefunden - initialisiere neu mit rule_engine")
        brain.protection_module = ProtectionModule(rule_engine)
    
    if not hasattr(brain, 'system_monitor') or brain.system_monitor is None:
        _LOG.info("system_monitor nicht in AIBrain gefunden - initialisiere neu")
        brain.system_monitor = SystemMonitor()
    
    # Initialisiere ModelCloner
    _LOG.info("Initialisiere ModelCloner...")
    model_cloner = ModelCloner(mm, brain.knowledge_base)
    
    # Initialisiere KnowledgeTransfer
    _LOG.info("Initialisiere KnowledgeTransfer...")
    knowledge_transfer = KnowledgeTransfer(
        brain.knowledge_base,
        brain.rule_engine,
        brain.protection_module
    )
    
    # Initialisiere ModelTrainer
    _LOG.info("Initialisiere ModelTrainer...")
    model_trainer = ModelTrainer(
        brain.knowledge_base,
        mm,
        {
            "epochs": 3,
            "batch_size": 8,
            "learning_rate": 5e-5
        }
    )
    
    # Registriere Lehrer-Modelle, falls vorhanden
    if hasattr(brain, 'model_orchestrator') and brain.model_orchestrator is not None:
        model_names = mm.list_models()
        if model_names:
            _LOG.info(f"Registriere {len(model_names)} Modelle als Lehrer-Modelle: {model_names}")
            for model_name in model_names:
                brain.model_orchestrator.register_teacher_model(model_name)
        else:
            _LOG.warning("Keine Modelle gefunden für Lehrer-Registrierung")
    
    autonomous_loop = None
    if enable_autonomy and AUTONOMY_AVAILABLE:
        try:
            _LOG.info("Initialisiere den autonomen Lernzyklus...")
            
            # Initialisiere den autonomen Lernzyklus
            autonomous_loop = AutonomousLoop(
                ai_engine=brain,
                knowledge_base=brain.knowledge_base,
                model_orchestrator=brain.model_orchestrator,
                rule_engine=brain.rule_engine,
                protection_module=brain.protection_module,
                model_manager=mm,
                system_monitor=brain.system_monitor,
                model_cloner=model_cloner,
                knowledge_transfer=knowledge_transfer,
                model_trainer=model_trainer,
                config={
                    "max_learning_cycles": 1000,
                    "learning_interval_seconds": 1800,  # Alle 30 Minuten
                    "min_confidence_threshold": 0.65,
                    "max_resource_usage": 0.85,
                    "max_goal_complexity": 5,
                    "safety_check_interval": 10,
                    "max_concurrent_learning_sessions": 1,
                    "min_knowledge_examples": 3,
                    "max_knowledge_examples": 10
                }
            )
            _LOG.info("Autonomer Lernzyklus erfolgreich initialisiert")
        except Exception as e:
            _LOG.error(f"Fehler bei der Initialisierung des autonomen Lernzyklus: {str(e)}", exc_info=True)
            autonomous_loop = None
    
    return brain, mm, pm, autonomous_loop, user_manager, auth_manager

def parse_args(argv=None):
    p = argparse.ArgumentParser(description='Mindestentinel - Autonomous AI System')
    p.add_argument("--start-rest", action="store_true", help="Start REST API (uvicorn)")
    p.add_argument("--start-ws", action="store_true", help="Start WebSocket API (uvicorn)")
    p.add_argument("--enable-autonomy", action="store_true", help="Aktiviert den autonomen Lernzyklus")
    p.add_argument("--api-host", default="0.0.0.0", help="API host address")
    p.add_argument("--api-port", default=8000, type=int, help="API port number")
    p.add_argument("--no-start", action="store_true", help="Init components but do not start any server")
    p.add_argument("--debug", action="store_true", help="Aktiviert Debug-Logging")
    return p.parse_args(argv)

def main():
    """Hauptfunktion des Programms."""
    # Prüfe, ob es ein Admin-Befehl ist
    if handle_admin_commands():
        return
    
    args = parse_args()
    
    # Debug-Modus aktivieren
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        _LOG.info("Debug-Modus aktiviert")
    
    # Sicherstellen, dass die Multiprocessing-Startmethode kompatibel ist
    try:
        if platform.system() == 'Windows':
            multiprocessing.set_start_method('spawn', force=True)
    except Exception as e:
        _LOG.warning(f"Multiprocessing-Startmethode konnte nicht gesetzt werden: {str(e)}")
    
    # Initialisiere alle Komponenten
    brain, mm, pm, autonomous_loop, user_manager, auth_manager = build_components(enable_autonomy=args.enable_autonomy)

    # Plugins aus dem plugins/ Verzeichnis laden
    try:
        loaded = pm.load_plugins_from_dir()
        _LOG.info("Plugins auto-loaded: %d", loaded)
    except Exception:
        _LOG.exception("Fehler beim Laden von Plugins")

    # Starte das Gehirn (Hintergrundloop etc.)
    brain.start()
    
    # Starte den autonomen Lernzyklus, wenn aktiviert und erfolgreich initialisiert
    if args.enable_autonomy and autonomous_loop is not None:
        _LOG.info("Aktiviere autonomen Lernzyklus...")
        autonomous_loop.start()
    
    if args.no_start:
        _LOG.info("System initialisiert (no-start). AIBrain läuft im Hintergrund. Exit.")
        return

    # Starte die API, falls gewünscht
    api_thread = None
    if args.start_rest:
        # Erstelle die REST API mit Authentifizierung
        app = create_app(brain, mm, pm, auth_manager)
        _LOG.info("Starting REST API on %s:%d", args.api_host, args.api_port)
        # Starte die REST API in einem separaten Thread, damit wir auf KeyboardInterrupt reagieren können
        api_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": args.api_host, "port": args.api_port}, daemon=True)
        api_thread.start()
    elif args.start_ws:
        # Erstelle die WebSocket API mit Authentifizierung
        app = create_ws_app(brain, auth_manager)
        _LOG.info("Starting WebSocket API on %s:%d", args.api_host, args.api_port)
        # Starte die WebSocket API in einem separaten Thread
        api_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": args.api_host, "port": args.api_port}, daemon=True)
        api_thread.start()
    else:
        _LOG.info("No API selected. Running in background. Use --start-rest or --start-ws to start servers.")
    
    # Haupt-Loop für das Warten auf Beendigung
    try:
        while True:
            # PRÜFE DEN AKTUELLEN ZUSTAND DES AUTONOMEN LOOP, NICHT DES START-THREADS
            if args.enable_autonomy and autonomous_loop is not None and not autonomous_loop.active:
                _LOG.info("Autonomer Lernzyklus beendet. Stoppe System.")
                break
                
            # Prüfe, ob die API-Threads noch laufen (falls gestartet)
            if api_thread and not api_thread.is_alive():
                _LOG.info("API-Server beendet. Stoppe System.")
                break
                
            # Warte kurz, bevor wir erneut prüfen
            time.sleep(1)
    except KeyboardInterrupt:
        _LOG.info("Received KeyboardInterrupt. Shutting down.")
    except Exception as e:
        _LOG.critical(f"Ungefangene Ausnahme im Hauptloop: {str(e)}", exc_info=True)
    
    finally:
        # Stoppe den autonomen Lernzyklus, wenn aktiv
        if args.enable_autonomy and autonomous_loop is not None and autonomous_loop.active:
            _LOG.info("Deaktiviere autonomen Lernzyklus...")
            autonomous_loop.stop()
        
        # Stoppe das Gehirn
        brain.stop()
        
        _LOG.info("System shutdown complete.")

if __name__ == "__main__":
    try:
        multiprocessing.freeze_support()
    except Exception:
        pass
    try:
        main()
    except Exception as e:
        _LOG.critical(f"Kritischer Fehler im Hauptprogramm: {str(e)}", exc_info=True)
        sys.exit(1)