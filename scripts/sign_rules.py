#!/usr/bin/env python3
"""Sign or verify config/rules.json using HMAC-SHA256.
Usage:
  python scripts/sign_rules.py sign   # generates key + signature (asks for passphrase optional)
  python scripts/sign_rules.py verify # verifies existing signature
"""
import sys, os, getpass
from pathlib import Path
import hmac, hashlib

ROOT = Path.cwd()
RULES = ROOT / 'config' / 'rules.json'
SIG = ROOT / 'config' / 'rules.sig'
KEY = ROOT / 'config' / 'rules_key.key'

def generate_key():
    # simple key generation - admin can replace with safer storage
    import secrets
    return secrets.token_bytes(32)

def sign():
    if not RULES.exists():
        print('No rules.json found at', RULES)
        return 1
    key = generate_key()
    mac = hmac.new(key, RULES.read_bytes(), hashlib.sha256).hexdigest()
    KEY.write_bytes(key)
    SIG.write_text(mac)
    print('Signed rules.json -> signature and key written to config/')
    return 0

def verify():
    if not (RULES.exists() and SIG.exists() and KEY.exists()):
        print('Missing files (rules.json, rules.sig, rules_key.key)')
        return 2
    key = KEY.read_bytes()
    mac = hmac.new(key, RULES.read_bytes(), hashlib.sha256).hexdigest()
    expected = SIG.read_text().strip()
    if hmac.compare_digest(mac, expected):
        print('OK: signature valid')
        return 0
    print('INVALID: signature mismatch')
    return 3

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: sign|verify')
        raise SystemExit(1)
    cmd = sys.argv[1].lower()
    if cmd == 'sign':
        raise SystemExit(sign())
    elif cmd == 'verify':
        raise SystemExit(verify())
    else:
        print('Unknown command')
        raise SystemExit(1)
