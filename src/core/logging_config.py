# src/core/logging_config.py
"""
Logging-Konfiguration für Mindestentinel

Diese Datei konfiguriert das Logging-System des Projekts.
Stellt sicher, dass Logs im richtigen Verzeichnis gespeichert werden.
"""

import logging
import os
from datetime import datetime

# Erstelle das Log-Verzeichnis im Projektwurzel
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

# Stelle sicher, dass das Log-Verzeichnis existiert
os.makedirs(LOG_DIR, exist_ok=True)

# Generiere Log-Dateinamen mit Datum
LOG_FILE = os.path.join(LOG_DIR, f"mindestentinel_{datetime.now().strftime('%Y%m%d')}.log")

def setup_logging():
    """
    Konfiguriert das Logging-System für das gesamte Projekt.
    
    Erstellt eine zentrale Logging-Konfiguration mit:
    - Datei-Logging in das Logs-Verzeichnis
    - Konsolen-Logging für Debugging
    - Formatierung mit Zeitstempel und Log-Level
    """
    # Basis-Logger konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    # Spezialisierte Logger konfigurieren
    logger_names = [
        "mindestentinel.main",
        "mindestentinel.ai_engine",
        "mindestentinel.autonomous_loop",
        "mindestentinel.knowledge_base",
        "mindestentinel.rule_engine",
        "mindestentinel.system_monitor",
        "mindestentinel.api"
    ]
    
    for name in logger_names:
        logger = logging.getLogger(name)
        logger.propagate = True
    
    # Debug-Logging für Entwicklung
    if os.getenv("DEBUG", "false").lower() == "true":
        logging.getLogger().setLevel(logging.DEBUG)
    
    logging.info(f"Logging konfiguriert. Logs werden gespeichert in: {LOG_FILE}")

def get_log_file_path():
    """
    Gibt den Pfad zur aktuellen Log-Datei zurück.
    
    Returns:
        str: Pfad zur Log-Datei
    """
    return LOG_FILE