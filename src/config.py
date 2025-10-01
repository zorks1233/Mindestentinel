# src/core/config.py
"""
config.py - Konfigurationsmanagement für Mindestentinel

Diese Datei lädt Konfigurationswerte aus Umgebungsvariablen oder einer .env-Datei.
"""

from __future__ import annotations
import os
from pathlib import Path
import logging
import time

logger = logging.getLogger("mindestentinel.config")

def setup_logging():
    """Richtet das Logging basierend auf der Konfiguration ein."""
    log_level = logging.INFO
    log_dir = Path("logs")
    
    # Erstelle das Log-Verzeichnis, falls nicht vorhanden
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Konfiguriere das Root-Logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / f"mindestentinel_{time.strftime('%Y%m%d')}.log"),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Logging konfiguriert. Logs werden gespeichert in: " + str(log_dir))
    
    # Setze das Logging-Level für spezifische Module
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

# Initialisiere das Logging
setup_logging()

# Allgemeine Konfiguration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# JWT-Konfiguration
MIND_JWT_SECRET = os.getenv("MIND_JWT_SECRET", "Ihr_geheimer_Schlüssel_hier")
MIND_JWT_ALG = os.getenv("MIND_JWT_ALG", "HS256")
MIND_JWT_EXP = int(os.getenv("MIND_JWT_EXP", "3600"))  # 1 Stunde

# Authentifizierungs-Konfiguration
REQUIRE_2FA = os.getenv("REQUIRE_2FA", "false").lower() == "true"
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_TIME = int(os.getenv("LOCKOUT_TIME", "300"))  # 5 Minuten

# Autonomie-Konfiguration
ENABLE_AUTONOMY = os.getenv("ENABLE_AUTONOMY", "false").lower() == "true"
LEARNING_INTERVAL = int(os.getenv("LEARNING_INTERVAL", "1800"))  # 30 Minuten
MAX_RESOURCE_USAGE = float(os.getenv("MAX_RESOURCE_USAGE", "0.85"))

def get_config() -> dict:
    """
    Gibt eine Zusammenfassung der aktuellen Konfiguration zurück.
    
    Returns:
        dict: Die Konfigurationswerte
    """
    return {
        "DEBUG": DEBUG,
        "API_HOST": API_HOST,
        "API_PORT": API_PORT,
        "MIND_JWT_ALG": MIND_JWT_ALG,
        "MIND_JWT_EXP": MIND_JWT_EXP,
        "REQUIRE_2FA": REQUIRE_2FA,
        "ENABLE_AUTONOMY": ENABLE_AUTONOMY,
        "LEARNING_INTERVAL": LEARNING_INTERVAL
    }