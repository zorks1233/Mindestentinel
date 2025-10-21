"""
protection_module.py
Modul für Sicherheits- und Schutzmechanismen im Mindestentinel-System.
Enthält die ProtectionModule-Klasse zur Initialisierung und Verwaltung von Schutzsystemen.
"""

import logging
import sys
import os
from typing import Optional, Any

# Dynamische Pfadermittlung basierend auf der tatsächlichen Projektstruktur
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
# Korrekte Berechnung: Von src/core zwei Ebenen nach oben zum Projekt-Root
project_root = os.path.dirname(os.path.dirname(current_dir))

# Füge das Projekt-Root zum Python-Pfad hinzu
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logging.debug(f"Projekt-Root zum Python-Pfad hinzugefügt: {project_root}")

# Debug-Ausgabe für Importpfade
logging.debug(f"Aktueller Python-Pfad: {sys.path}")
logging.debug(f"Projekt-Root: {project_root}")
logging.debug(f"Suche nach config-Verzeichnis in: {os.path.join(project_root, 'config')}")

# Prüfe, ob config-Verzeichnis existiert
config_dir = os.path.join(project_root, 'config')
if not os.path.exists(config_dir):
    logging.critical(f"config-Verzeichnis nicht gefunden: {config_dir}")
    # Versuche alternative Struktur (falls Projekt-Root falsch berechnet)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    config_dir = os.path.join(project_root, 'config')
    if not os.path.exists(config_dir):
        raise RuntimeError(f"config-Verzeichnis nicht gefunden: {config_dir}")
    else:
        logging.info(f"Alternative Projekt-Root gefunden: {project_root}")
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

# Prüfe, ob config_loader.py existiert
config_loader_path = os.path.join(config_dir, 'config_loader.py')
if not os.path.exists(config_loader_path):
    logging.critical(f"config_loader.py nicht gefunden: {config_loader_path}")
    # Versuche alternative Pfade
    alt_paths = [
        os.path.join(os.path.dirname(project_root), 'config', 'config_loader.py'),
        os.path.join(project_root, 'src', 'config', 'config_loader.py')
    ]
    for path in alt_paths:
        if os.path.exists(path):
            config_loader_path = path
            logging.info(f"Verwende alternative config_loader.py: {config_loader_path}")
            break
    else:
        raise RuntimeError(f"config_loader.py nicht gefunden an erwarteten Orten")

# Import der Konfigurationskomponenten
try:
    # Versuche, config.config_loader aus dem Projekt-Root zu importieren
    from config.config_loader import ConfigLoader
    logging.debug("Erfolgreich importiert: config.config_loader")
except ImportError as e:
    logging.error(f"Fehler beim Import von config.config_loader: {str(e)}")
    # Manuelles Laden der Datei als letzte Option
    import importlib.util
    spec = importlib.util.spec_from_file_location("config.config_loader", config_loader_path)
    config_loader = importlib.util.module_from_spec(spec)
    sys.modules["config.config_loader"] = config_loader
    spec.loader.exec_module(config_loader)
    ConfigLoader = config_loader.ConfigLoader
    logging.debug("Erfolgreich manuell geladen: config.config_loader")

# Import der RuleEngine
try:
    from core.rule_engine import RuleEngine
except ImportError:
    try:
        from rule_engine import RuleEngine
    except ImportError:
        logging.warning("RuleEngine-Modul nicht gefunden - wird später initialisiert")
        RuleEngine = None

class ProtectionModule:
    """
    Hauptklasse für das Schutzsystem des Mindestentinel-Frameworks.
    Verwaltet Sicherheitsprotokolle, Zugriffskontrollen und Regelbasierte Schutzmechanismen.
    """
    
    def __init__(self, rule_engine: Optional[RuleEngine] = None, config: Optional[dict] = None):
        """
        Initialisiert das ProtectionModule.
        
        Args:
            rule_engine: Optional bereitgestellte RuleEngine-Instanz
            config: Optionale Konfigurationsparameter
        """
        self.logger = logging.getLogger("mindestentinel.protection")
        self.logger.info("Initialisiere ProtectionModule...")
        
        # Konfiguration laden
        try:
            self.config = config or ConfigLoader.load_config('protection')
            self.logger.debug("Konfiguration erfolgreich geladen")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
            self.config = {
                'rules': {},
                'systems': []
            }
        
        self.rule_engine = rule_engine
        
        # Regel-Engine initialisieren, falls nicht bereitgestellt
        if self.rule_engine is None:
            self.logger.debug("Keine RuleEngine übergeben, versuche Initialisierung")
            if RuleEngine is None:
                try:
                    from core.rule_engine import RuleEngine
                except ImportError:
                    try:
                        from rule_engine import RuleEngine
                    except ImportError:
                        raise RuntimeError("RuleEngine-Modul konnte nicht importiert werden") from None
            
            try:
                self.rule_engine = RuleEngine(config=self.config.get('rules', {}))
                self.logger.info("RuleEngine erfolgreich initialisiert")
            except Exception as e:
                self.logger.error(f"Fehler bei RuleEngine-Initialisierung: {str(e)}")
                raise RuntimeError("Konnte RuleEngine nicht initialisieren") from e
        
        # Schutzsysteme laden
        self._load_protection_systems()
    
    def _load_protection_systems(self) -> None:
        """
        Lädt und initialisiert alle konfigurierten Schutzsysteme.
        """
        protection_systems = self.config.get('systems', [])
        self.logger.info(f"Lade {len(protection_systems)} Schutzsysteme")
        
        for system in protection_systems:
            system_name = system.get('name', 'Unknown')
            self.logger.debug(f"Initialisiere Schutzsystem: {system_name}")
            # Hier würden die konkreten Schutzsysteme initialisiert werden
            # Beispiel: self._initialize_system(system)
    
    def check_access(self, user: Any, resource: str, action: str) -> bool:
        """
        Überprüft, ob ein Benutzer auf eine Ressource mit einer bestimmten Aktion zugreifen darf.
        
        Args:
            user: Der Benutzer oder seine Identifikationsdaten
            resource: Die Ressource, auf die zugegriffen werden soll
            action: Die Aktion, die ausgeführt werden soll
            
        Returns:
            bool: True, wenn der Zugriff erlaubt ist, sonst False
        """
        self.logger.debug(f"Überprüfe Zugriff: {user} -> {resource} ({action})")
        try:
            # Hier würde die eigentliche Zugriffsprüfung stattfinden
            # Beispiel: return self.rule_engine.evaluate(user, resource, action)
            return True  # Platzhalter - ersetzen Sie dies mit Ihrer Implementierung
        except Exception as e:
            self.logger.error(f"Fehler bei Zugriffsprüfung: {str(e)}")
            return False
    
    def apply_protection_rules(self, data: Any) -> Any:
        """
        Wendet Schutzregeln auf die bereitgestellten Daten an.
        
        Args:
            data: Die zu schützenden Daten
            
        Returns:
            Any: Geschützte/transformierte Daten
        """
        self.logger.debug("Wende Schutzregeln auf Daten an")
        try:
            # Hier würden die Schutzregeln angewendet werden
            # Beispiel: return self.rule_engine.process(data)
            return data  # Platzhalter - ersetzen Sie dies mit Ihrer Implementierung
        except Exception as e:
            self.logger.error(f"Fehler bei Anwendung von Schutzregeln: {str(e)}")
            raise