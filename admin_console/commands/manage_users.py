#!/usr/bin/env python3
"""
manage_users.py - Verwaltet Benutzerkonten

Dieses Skript ermöglicht das Erstellen, Auflisten und Löschen von Benutzerkonten.
"""

import sys
import argparse
import logging
from pathlib import Path
import os
import hashlib
import secrets
from datetime import datetime

# Füge Projekt-Root zum Python-Pfad hinzu
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.knowledge_base import KnowledgeBase

# Setze Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mindestentinel.manage_users")

def create_user(username: str, password: str, is_admin: bool = False):
    """Erstellt einen neuen Benutzer"""
    # Prüfe, ob Benutzername bereits existiert
    kb = KnowledgeBase()
    existing = kb.query(
        "SELECT * FROM users WHERE username = ?", 
        (username,)
    )
    
    if existing:
        logger.error(f"Benutzer '{username}' existiert bereits")
        return False
    
    # Hash das Passwort
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    # Erstelle Benutzer
    user = {
        "username": username,
        "password_hash": password_hash,
        "salt": salt,
        "is_admin": int(is_admin),
        "created_at": datetime.now().isoformat(),
        "last_login": None
    }
    
    # Speichere Benutzer
    kb.store("users", user)
    logger.info(f"Benutzer '{username}' wurde erfolgreich erstellt")
    return True

def list_users():
    """Listet alle Benutzer auf"""
    kb = KnowledgeBase()
    users = kb.query("SELECT username, is_admin, created_at FROM users")
    
    if not users:
        logger.info("Keine Benutzer gefunden")
        return
    
    logger.info("Gefundene Benutzer:")
    for user in users:
        admin_status = "Admin" if user[1] else "Benutzer"
        logger.info(f"- {user[0]} ({admin_status}, erstellt: {user[2]})")

def delete_user(username: str):
    """Löscht einen Benutzer"""
    kb = KnowledgeBase()
    
    # Prüfe, ob Benutzer existiert
    user = kb.query(
        "SELECT * FROM users WHERE username = ?", 
        (username,)
    )
    
    if not user:
        logger.error(f"Benutzer '{username}' existiert nicht")
        return False
    
    # Lösche Benutzer
    kb.delete("users", f"username = '{username}'")
    logger.info(f"Benutzer '{username}' wurde erfolgreich gelöscht")
    return True

def main():
    parser = argparse.ArgumentParser(description='Verwalte Benutzerkonten')
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Befehle')
    
    # Create-Befehl
    create_parser = subparsers.add_parser('create', help='Erstelle einen neuen Benutzer')
    create_parser.add_argument('--username', required=True, help='Benutzername')
    create_parser.add_argument('--password', required=True, help='Passwort')
    create_parser.add_argument('--admin', action='store_true', help='Benutzer als Administrator markieren')
    
    # List-Befehl
    subparsers.add_parser('list', help='Liste alle Benutzer auf')
    
    # Delete-Befehl
    delete_parser = subparsers.add_parser('delete', help='Lösche einen Benutzer')
    delete_parser.add_argument('--username', required=True, help='Zu löschender Benutzername')
    
    args = parser.parse_args()
    
    if args.command == 'create':
        create_user(args.username, args.password, args.admin)
    elif args.command == 'list':
        list_users()
    elif args.command == 'delete':
        delete_user(args.username)
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())