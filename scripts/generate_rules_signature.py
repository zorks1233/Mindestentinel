"""
generate_rules_signature.py
Generiert eine kryptografische Signatur für die Regeldatei.
Stellt sicher, dass die Regeln nicht manipuliert wurden.
"""

import os
import hashlib
import hmac
import logging
from pathlib import Path

# Konfiguration
KEY_FILE = "config/rules_key.key"
RULES_FILE = "config/rules.yaml"
SIGNATURE_FILE = "config/rules.sig"

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("generate_rules_signature")

def ensure_directory_exists(path: str) -> None:
    """Stellt sicher, dass das Verzeichnis existiert"""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Verzeichnis erstellt: {directory}")

def generate_key() -> bytes:
    """Generiert einen sicheren kryptografischen Schlüssel"""
    return os.urandom(32)

def save_key(key: bytes, key_path: str) -> None:
    """Speichert den Schlüssel in einer Datei"""
    ensure_directory_exists(key_path)
    with open(key_path, 'wb') as f:
        f.write(key)
    logger.info(f"Sicherer Schlüssel gespeichert: {key_path}")

def load_key(key_path: str) -> bytes:
    """Lädt den Schlüssel aus einer Datei"""
    with open(key_path, 'rb') as f:
        return f.read()

def generate_signature(rules_path: str, key: bytes) -> str:
    """Generiert eine Signatur für die Regeldatei"""
    with open(rules_path, 'rb') as f:
        rules_data = f.read()
    return hmac.new(key, rules_data, hashlib.sha256).hexdigest()

def save_signature(signature: str, sig_path: str) -> None:
    """Speichert die Signatur in einer Datei"""
    ensure_directory_exists(sig_path)
    with open(sig_path, 'w') as f:
        f.write(signature)
    logger.info(f"Signatur gespeichert: {sig_path}")

def find_project_root() -> str:
    """Findet das Projekt-Root-Verzeichnis"""
    current_dir = os.getcwd()
    
    # Prüfe, ob wir uns bereits im Projekt-Root befinden
    if os.path.exists(os.path.join(current_dir, "config", "rules.yaml")):
        return current_dir
    
    # Prüfe das übergeordnete Verzeichnis
    parent_dir = os.path.dirname(current_dir)
    if os.path.exists(os.path.join(parent_dir, "config", "rules.yaml")):
        return parent_dir
    
    # Prüfe das src-Verzeichnis
    if os.path.exists(os.path.join(current_dir, "src", "config", "rules.yaml")):
        return current_dir
    
    # Fallback: Verwende das aktuelle Verzeichnis
    return current_dir

def main():
    """Hauptfunktion des Skripts"""
    logger.info("Starte Regel-Signatur-Generierung...")
    
    # Finde das Projekt-Root
    project_root = find_project_root()
    logger.debug(f"Gefundenes Projekt-Root: {project_root}")
    
    # Pfade anpassen
    key_path = os.path.join(project_root, KEY_FILE)
    rules_path = os.path.join(project_root, RULES_FILE)
    sig_path = os.path.join(project_root, SIGNATURE_FILE)
    
    logger.debug(f"Verwende Regelpfad: {rules_path}")
    
    # Prüfe, ob Regeldatei existiert
    if not os.path.exists(rules_path):
        logger.error(f"❌ Regeldatei nicht gefunden: {rules_path}")
        logger.info("Bitte erstellen Sie eine Regeldatei unter config/rules.yaml")
        return
    
    # Erstelle Schlüssel, falls nicht vorhanden
    if not os.path.exists(key_path):
        logger.info(f"ℹ️  Generiere neuen Sicherheitsschlüssel: {key_path}")
        key = generate_key()
        save_key(key, key_path)
    else:
        logger.info(f"ℹ️  Sicherer Schlüssel existiert bereits: {key_path}")
        key = load_key(key_path)
    
    # Generiere und speichere Signatur
    signature = generate_signature(rules_path, key)
    save_signature(signature, sig_path)
    
    logger.info("✅ Regel-Signatur-Setup abgeschlossen!")
    logger.info("Ihr System sollte jetzt ohne Signatur-Fehler starten.")

if __name__ == "__main__":
    main()