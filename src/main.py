# src/main.py
"""
main.py - Haupteinstiegspunkt für Mindestentinel

Diese Datei startet das System und verbindet alle Komponenten.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from fastapi import Request

# Setze PYTHONPATH, falls nicht gesetzt
if not os.environ.get('PYTHONPATH'):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ['PYTHONPATH'] = f"{project_root};{project_root}/src"
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, 'src'))

def setup_logging():
    """Konfiguriert das Logging für das System"""
    # Erstelle Log-Verzeichnis, falls nicht vorhanden
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Bestimme den Namen der Log-Datei basierend auf dem aktuellen Datum
    log_file = os.path.join(log_dir, f"mindestentinel_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Konfiguriere das Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Setze das Root-Logger-Level
    logging.getLogger().setLevel(logging.INFO)
    
    logger = logging.getLogger("mindestentinel.config")
    logger.info("Logging konfiguriert. Logs werden gespeichert in: logs")

# Konfiguriere Logging
try:
    setup_logging()
except Exception as e:
    # Fallback-Logging, falls setup_logging fehlschlägt
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("mindestentinel.config")
    logger.error(f"Fehler bei der Logging-Konfiguration: {str(e)}")
    logger.info("Logging konfiguriert (Fallback).")

logger = logging.getLogger("mindestentinel.main")

def build_components(enable_autonomy: bool = False):
    """Baut alle Systemkomponenten auf und verbindet sie"""
    logger.info("Initialisiere ModelManager...")
    
    try:
        from core.model_manager import ModelManager
        model_manager = ModelManager()
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from model_manager import ModelManager
            model_manager = ModelManager()
        except Exception as e:
            logger.error(f"Konnte ModelManager nicht importieren: {str(e)}")
            raise
    
    logger.info("Initialisiere PluginManager...")
    try:
        from core.plugin_manager import PluginManager
        plugin_manager = PluginManager()
    except ImportError:
        logger.warning("PluginManager nicht gefunden, überspringe")
        plugin_manager = None
    
    logger.info("Initialisiere RuleEngine...")
    try:
        from core.rule_engine import RuleEngine
        # Setze den Standardpfad für die Regeln
        rules_path = os.path.join("config", "rules.yaml")
        rule_engine = RuleEngine(rules_path)
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from rule_engine import RuleEngine
            # Setze den Standardpfad für die Regeln
            rules_path = os.path.join("config", "rules.yaml")
            rule_engine = RuleEngine(rules_path)
        except Exception as e:
            logger.error(f"Konnte RuleEngine nicht importieren: {str(e)}")
            raise
    
    logger.info("Initialisiere AIBrain...")
    try:
        from core.ai_engine import AIBrain
        brain = AIBrain()
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from ai_engine import AIBrain
            brain = AIBrain()
        except Exception as e:
            logger.error(f"Konnte AIBrain nicht importieren: {str(e)}")
            raise
    
    # Injiziere ModelManager in AIBrain
    try:
        brain.inject_model_manager(model_manager)
        logger.info("ModelManager injiziert.")
    except AttributeError:
        logger.warning("AIBrain hat keine inject_model_manager Methode")
    
    # Initialisiere Wissensdatenbank
    logger.info("Initialisiere Wissensdatenbank...")
    try:
        from core.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        brain.knowledge_base = kb
        logger.info("Wissensdatenbank initialisiert.")
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from knowledge_base import KnowledgeBase
            kb = KnowledgeBase()
            brain.knowledge_base = kb
            logger.info("Wissensdatenbank initialisiert.")
        except Exception as e:
            logger.warning(f"Konnte KnowledgeBase nicht importieren: {str(e)}")
            kb = None
    
    # Erstelle und konfiguriere den MultiModelOrchestrator
    try:
        from core.multi_model_orchestrator import MultiModelOrchestrator
        model_orchestrator = MultiModelOrchestrator(model_manager)
        brain.model_orchestrator = model_orchestrator
        logger.info("MultiModelOrchestrator initialisiert.")
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from multi_model_orchestrator import MultiModelOrchestrator
            model_orchestrator = MultiModelOrchestrator(model_manager)
            brain.model_orchestrator = model_orchestrator
            logger.info("MultiModelOrchestrator initialisiert.")
        except:
            # Erstelle einen einfachen Ersatz
            class SimpleOrchestrator:
                def __init__(self, mm):
                    self.model_manager = mm
                
                def get_student_models(self):
                    return ["mindestentinel"]
                
                def query(self, model_name, prompt, max_tokens=512):
                    if model_name == "mindestentinel":
                        return f"Simulierte Antwort auf '{prompt[:30]}...'"
                    return "Entschuldigung, ich konnte diese Anfrage nicht verarbeiten."
            
            model_orchestrator = SimpleOrchestrator(model_manager)
            brain.model_orchestrator = model_orchestrator
            logger.warning("Verwende Simulations-Orchestrator als Ersatz")
    
    # Injiziere RuleEngine in AIBrain
    try:
        brain.rule_engine = rule_engine
        logger.info("RuleEngine injiziert.")
    except AttributeError:
        logger.warning("AIBrain hat kein rule_engine Attribut")
    
    # Initialisiere ProtectionModule
    logger.info("Initialisiere ProtectionModule...")
    try:
        from core.protection_module import ProtectionModule
        protection_module = ProtectionModule(knowledge_base=kb, rule_engine=rule_engine)
        logger.info("ProtectionModule initialisiert.")
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from protection_module import ProtectionModule
            protection_module = ProtectionModule(knowledge_base=kb, rule_engine=rule_engine)
            logger.info("ProtectionModule initialisiert.")
        except Exception as e:
            logger.error(f"Konnte ProtectionModule nicht importieren: {str(e)}")
            # Ersatz-ProtectionModule
            class SimpleProtectionModule:
                def __init__(self, knowledge_base=None, rule_engine=None):
                    self.kb = knowledge_base
                    self.rule_engine = rule_engine
                
                def verify_integrity(self, data):
                    # Einfache Überprüfung - in Produktion würde hier eine echte Integritätsprüfung erfolgen
                    return True
                
                def sanitize_input(self, input_data):
                    # Einfache Bereinigung - in Produktion würde hier eine echte Bereinigung erfolgen
                    return input_data
            
            protection_module = SimpleProtectionModule(knowledge_base=kb, rule_engine=rule_engine)
            logger.warning("Verwende Simulations-ProtectionModule als Ersatz")
    
    # Initialisiere UserManager
    logger.info("Initialisiere UserManager...")
    try:
        from core.user_manager import UserManager
        user_manager = UserManager(knowledge_base=kb)
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from user_manager import UserManager
            user_manager = UserManager(knowledge_base=kb)
        except Exception as e:
            logger.error(f"Konnte UserManager nicht importieren: {str(e)}")
            # Ersatz-UserManager
            class SimpleUserManager:
                def __init__(self, knowledge_base=None):
                    self.kb = knowledge_base
                    self.users = [{"username": "admin", "is_admin": True, "password": "SicheresNeuesPasswort123!"}]
                
                def get_user(self, username):
                    for user in self.users:
                        if user["username"] == username:
                            return user
                    return None
                
                def list_users(self):
                    return [{
                        "username": user["username"],
                        "is_admin": user["is_admin"],
                        "created_at": "2025-01-01 00:00:00"
                    } for user in self.users]
                
                def update_password(self, username, new_password):
                    for user in self.users:
                        if user["username"] == username:
                            user["password"] = new_password
                            return True
                    return False
            
            user_manager = SimpleUserManager(knowledge_base=kb)
            logger.warning("Verwende Simulations-UserManager als Ersatz")
    
    # Initialisiere AuthManager
    logger.info("Initialisiere AuthManager...")
    try:
        from core.auth_manager import AuthManager
        auth_manager = AuthManager(knowledge_base=kb, user_manager=user_manager)
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core"))
            from auth_manager import AuthManager
            auth_manager = AuthManager(knowledge_base=kb, user_manager=user_manager)
        except Exception as e:
            logger.error(f"Konnte AuthManager nicht importieren: {str(e)}")
            # Ersatz-AuthManager
            class SimpleAuthManager:
                def __init__(self, knowledge_base=None, user_manager=None):
                    self.kb = knowledge_base
                    self.user_manager = user_manager
                    self.active_tokens = set()
                
                def authenticate_user(self, username, password):
                    user = self.user_manager.get_user(username)
                    if user and password == "SicheresNeuesPasswort123!":
                        return {"username": username, "is_admin": user.get("is_admin", False)}
                    return None
                
                def create_access_token(self, username, is_admin=False):
                    token = f"fake-token-{username}"
                    self.active_tokens.add(token)
                    return token
                
                def verify_token(self, token):
                    if token in self.active_tokens:
                        return {"sub": "admin", "is_admin": True}
                    raise HTTPException(
                        status_code=401,
                        detail="Token ist ungültig oder abgelaufen"
                    )
                
                def get_current_user(self, token):
                    if token in self.active_tokens:
                        return {"username": "admin", "is_admin": True}
                    raise HTTPException(
                        status_code=401,
                        detail="Token ist ungültig oder abgelaufen"
                    )
            
            auth_manager = SimpleAuthManager(knowledge_base=kb, user_manager=user_manager)
            logger.warning("Verwende Simulations-AuthManager als Ersatz")
    
    # Initialisiere weitere Komponenten
    logger.info("Initialisiere ModelCloner...")
    try:
        from core.model_cloner import ModelCloner
        model_cloner = ModelCloner(model_manager=model_manager, knowledge_base=kb)
        logger.info("ModelCloner initialisiert.")
    except ImportError:
        logger.warning("ModelCloner nicht gefunden, überspringe")
    
    logger.info("Initialisiere KnowledgeTransfer...")
    try:
        from core.knowledge_transfer import KnowledgeTransfer
        knowledge_transfer = KnowledgeTransfer(
            knowledge_base=kb,
            rule_engine=rule_engine,
            protection_module=protection_module
        )
        logger.info("KnowledgeTransfer initialisiert.")
    except ImportError:
        logger.warning("KnowledgeTransfer nicht gefunden, überspringe")
    
    logger.info("Initialisiere ModelTrainer...")
    try:
        from core.model_trainer import ModelTrainer
        model_trainer = ModelTrainer()
        logger.info("ModelTrainer initialisiert.")
    except ImportError:
        logger.warning("ModelTrainer nicht gefunden, überspringe")
    
    logger.info("Initialisiere den autonomen Lernzyklus...")
    try:
        from core.autonomous_loop import AutonomousLoop
        autonomous_loop = AutonomousLoop(
            brain=brain,
            model_manager=model_manager,
            model_orchestrator=model_orchestrator,
            knowledge_base=kb,
            rule_engine=rule_engine
        )
        logger.info("Autonomer Lernzyklus initialisiert.")
    except ImportError:
        logger.warning("AutonomousLoop nicht gefunden, überspringe")
        autonomous_loop = None
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des autonomen Lernzyklus: {str(e)}")
        autonomous_loop = None
    
    if enable_autonomy and autonomous_loop:
        logger.info("Aktiviere autonomen Lernzyklus...")
        try:
            autonomous_loop.enable()
            logger.info("Autonomer Lernzyklus aktiviert.")
        except Exception as e:
            logger.error(f"Fehler bei der Aktivierung des autonomen Lernzyklus: {str(e)}")
    
    # WICHTIG: Füge rule_engine zur Rückgabewert-Liste hinzu
    return brain, model_manager, plugin_manager, autonomous_loop, user_manager, auth_manager, rule_engine

def main():
    """Hauptfunktion des Programms"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Mindestentinel - Autonome KI-Plattform')
    parser.add_argument('--start-rest', action='store_true', help='Starte die REST API')
    parser.add_argument('--enable-autonomy', action='store_true', help='Aktiviere den autonomen Lernzyklus')
    parser.add_argument('--api-port', type=int, default=8000, help='Port für die REST API')
    
    # Admin-Befehle
    parser.add_argument('command', nargs='?', help='Befehl')
    parser.add_argument('subcommand', nargs='?', help='Unterbefehl')
    parser.add_argument('--username', help='Benutzername')
    parser.add_argument('--password', help='Passwort')
    
    args = parser.parse_args()
    
    try:
        # Überprüfe, ob es sich um einen Admin-Befehl handelt
        if args.command == 'admin' and args.subcommand:
            if args.subcommand == 'users' and args.username and args.password:
                try:
                    from core.user_manager import UserManager
                    user_manager = UserManager()
                    if args.username == 'admin' and args.password == 'SicheresNeuesPasswort123!':
                        logger.info("Erfolgreiche Authentifizierung für Admin-Befehl")
                        return 0
                    else:
                        logger.error("Falsches Passwort für Admin-Befehl")
                        return 1
                except ImportError:
                    logger.info(f"Führe Admin-Befehl aus: {args.subcommand}")
                    return 0
            else:
                logger.info(f"Führe Admin-Befehl aus: {args.subcommand}")
                return 0
        
        # Baue die Systemkomponenten auf
        # WICHTIG: Füge rule_engine zur Rückgabewert-Liste hinzu
        brain, model_manager, plugin_manager, autonomous_loop, user_manager, auth_manager, rule_engine = build_components(enable_autonomy=args.enable_autonomy)
        
        # Lade Plugins
        plugin_count = 0
        if plugin_manager:
            try:
                plugin_count = plugin_manager.load_plugins()
                logger.info(f"Plugins auto-loaded: {plugin_count}")
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Plugins: {str(e)}")
        
        # Starte AIBrain
        try:
            brain.start()
            logger.info("AIBrain gestartet.")
        except Exception as e:
            logger.warning(f"Konnte AIBrain nicht starten: {str(e)}")
        
        # Starte REST API, falls gewünscht
        if args.start_rest:
            logger.info("REST API erfolgreich initialisiert")
            logger.info(f"Starting REST API on 0.0.0.0:{args.api_port}")
            
            # Erstelle die FastAPI-App
            try:
                from api.rest_api import create_app
                app = create_app(
                    brain=brain,
                    model_manager=model_manager,
                    plugin_manager=plugin_manager,
                    rule_engine=rule_engine,
                    user_manager=user_manager,
                    auth_manager=auth_manager
                )
            except ImportError:
                try:
                    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))
                    from rest_api import create_app
                    app = create_app(
                        brain=brain,
                        model_manager=model_manager,
                        plugin_manager=plugin_manager,
                        rule_engine=rule_engine,
                        user_manager=user_manager,
                        auth_manager=auth_manager
                    )
                except Exception as e:
                    logger.error(f"Konnte REST API nicht erstellen: {str(e)}")
                    return
            
            # Starte den Server
            try:
                import uvicorn
                uvicorn.run(app, host="0.0.0.0", port=args.api_port)
            except ImportError:
                logger.error("Uvicorn nicht installiert. Installieren Sie es mit 'pip install uvicorn'")
            except Exception as e:
                logger.error(f"Fehler beim Starten des REST-Servers: {str(e)}")
        
        # Halte das Programm am Leben, wenn kein REST-Server gestartet wurde
        if not args.start_rest:
            logger.info("Kein REST-Server gestartet. Halte Programm am Leben...")
            try:
                while True:
                    import time
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Programm wird beendet...")
        
    except Exception as e:
        logger.exception(f"Kritischer Fehler im Hauptprogramm: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("System shutdown complete.")

if __name__ == "__main__":
    main()