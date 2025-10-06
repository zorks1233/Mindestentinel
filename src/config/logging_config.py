# src/config/logging_config.py
"""
Logging-Konfiguration für Mindestentinel

Diese Datei konfiguriert das Logging-System des Projekts.
"""

import logging
import os
from datetime import datetime

def setup_logging():
    """
    Konfiguriert das Logging-System
    
    - Erstellt das Log-Verzeichnis, falls nicht vorhanden
    - Konfiguriert File- und Console-Handler
    - Setzt das Logging-Format
    """
    # Bestimme das Projekt-Root absolut
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Erstelle das Log-Verzeichnis im Projekt-Root
    log_dir = os.path.join(project_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Erstelle den Log-Dateinamen mit aktuellem Datum
    log_file = os.path.join(log_dir, f"mindestentinel_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Konfiguriere das Root-Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Setze das Logging-Level für bestimmte Module
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Bestätigung
    logging.info(f"Logging konfiguriert. Ausgabe wird geschrieben nach: {log_file}")