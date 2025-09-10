#!/usr/bin/env python3
"""
Signiert die Regeldatei mit HMAC-SHA256
Verwendung: python scripts/sign_rules.py config/rules.yaml
"""

import hmac
import hashlib
import argparse
from pathlib import Path
import os
import logging

# Setze Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sign_rules")

def sign(rules_path: Path, key_path: Path, sig_path: Path):
    """Signiert die Regeldatei"""
    try:
        # Generiere einen sicheren Schlüssel (32 Bytes)
        key = os.urandom(32)
        key_path.write_bytes(key)
        logger.info(f"Signaturschlüssel erzeugt: {key_path}")
        
        # Prüfe, ob Regeldatei existiert
        if not rules_path.exists():
            logger.error(f"Regeldatei nicht gefunden: {rules_path}")
            return False
            
        # Signiere die Regeldatei
        data = rules_path.read_bytes()
        mac = hmac.new(key, data, hashlib.sha256).hexdigest()
        sig_path.write_text(mac)
        
        logger.info(f"Regeldatei signiert: {rules_path}")
        logger.info(f"Signaturschlüssel gespeichert: {key_path}")
        logger.info(f"Signatur gespeichert: {sig_path}")
        return True
    except Exception as e:
        logger.error(f"Fehler bei der Signaturerstellung: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Signiert die Regeldatei')
    parser.add_argument("rules", help="Pfad zur Regeldatei (z.B. config/rules.yaml)")
    parser.add_argument("--key", default="config/rules_key.key", help="Pfad zum Signaturschlüssel")
    parser.add_argument("--sig", default="config/rules.sig", help="Pfad zur Signaturdatei")
    
    args = parser.parse_args()
    
    rules_path = Path(args.rules)
    key_path = Path(args.key)
    sig_path = Path(args.sig)
    
    # Erstelle config-Verzeichnis, falls nicht vorhanden
    rules_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Führe die Signatur durch
    success = sign(rules_path, key_path, sig_path)
    
    if not success:
        logger.error("Signaturerstellung fehlgeschlagen")
        exit(1)