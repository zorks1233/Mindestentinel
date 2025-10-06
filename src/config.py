# src/config.py
"""
config.py - Konfigurationsmanagement für Mindestentinel

Diese Datei verwaltet die Konfiguration des Systems.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("mindestentinel.config")

def setup_logging(log_dir: str = "logs") -> None:
    """
    Konfiguriert das Logging für das System
    
    Args:
        log_dir: Verzeichnis für Log-Dateien
    """
    # Erstelle Log-Verzeichnis, falls nicht vorhanden
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
    
    logger.info(f"Logging konfiguriert. Logs werden gespeichert in: {log_dir}")

def load_config():
    """Lädt die Konfiguration aus Umgebungsvariablen und .env-Datei"""
    # Lade .env-Datei, falls vorhanden
    env_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / '.env'
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Konfiguration aus .env-Datei geladen: {env_path}")
        except ImportError:
            logger.warning("python-dotenv nicht installiert. Kann .env-Datei nicht laden.")
    
    # Logging-Konfiguration
    log_dir = os.getenv("LOG_DIR", "logs")
    
    # API-Konfiguration
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    
    # JWT-Konfiguration
    jwt_secret = os.getenv("MIND_JWT_SECRET")
    if not jwt_secret:
        logger.warning("MIND_JWT_SECRET nicht gesetzt. Verwende generierten Schlüssel (NICHT FÜR PRODUKTION)")
        jwt_secret = os.urandom(32).hex()
        os.environ["MIND_JWT_SECRET"] = jwt_secret
    else:
        logger.info("MIND_JWT_SECRET aus Umgebungsvariablen geladen")
    
    return {
        "log_dir": log_dir,
        "api_host": api_host,
        "api_port": api_port,
        "jwt_secret": jwt_secret
    }