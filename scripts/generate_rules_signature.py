# generate_rules_signature.py
import os
import hmac
import hashlib
import secrets

# Pfade zu den Regel-Dateien
rules_path = "../config/rules.yaml"
key_path = "../config/rules_key.key"
sig_path = "../config/rules.sig"

# Stelle sicher, dass das config-Verzeichnis existiert
os.makedirs("../config", exist_ok=True)

# 1. Generiere einen sicheren Schlüssel, falls nicht vorhanden
if not os.path.exists(key_path):
    key = secrets.token_bytes(32)  # 256-bit Schlüssel
    with open(key_path, 'wb') as f:
        f.write(key)
    print(f"✅ Sicherer Schlüssel wurde erstellt: {key_path}")
else:
    print(f"ℹ️  Sicherer Schlüssel existiert bereits: {key_path}")

# 2. Generiere die Signatur für die Regeldatei
if not os.path.exists(rules_path):
    print(f"❌ Regeldatei nicht gefunden: {rules_path}")
    print("Bitte erstellen Sie eine Regeldatei unter config/rules.yaml")
else:
    # Lade den Schlüssel
    with open(key_path, 'rb') as f:
        key = f.read()
    
    # Berechne die Signatur
    with open(rules_path, 'rb') as f:
        data = f.read()
        signature = hmac.new(key, data, hashlib.sha256).hexdigest()
    
    # Speichere die Signatur
    with open(sig_path, 'w') as f:
        f.write(signature)
    
    print(f"✅ Signatur für Regeldatei wurde erstellt: {sig_path}")
    print(f"   Signatur: {signature}")

print("\n✅ Regel-Signatur-Setup abgeschlossen!")
print("Ihr System sollte jetzt ohne Signatur-Fehler starten.")