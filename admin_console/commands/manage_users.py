# admin_console/commands/manage_users.py
"""
Verwaltet Benutzerkonten über die Kommandozeile
"""

import argparse
from src.core.user_manager import UserManager
from src.core.knowledge_base import KnowledgeBase
import logging
import os
import sys

# Setze PYTHONPATH automatisch auf das Projekt-Root, falls nicht gesetzt
if "PYTHONPATH" not in os.environ:
    # Bestimme das Projekt-Root (angenommen, dass src/ im Projekt-Root liegt)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ["PYTHONPATH"] = project_root
    sys.path.insert(0, project_root)
    logging.info(f"PYTHONPATH automatisch gesetzt auf: {project_root}")

# Setze Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mindestentinel.manage_users")

def main():
    parser = argparse.ArgumentParser(description="Benutzerverwaltung für Mindestentinel")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # create command
    create_parser = subparsers.add_parser("create", help="Erstellt einen neuen Benutzer")
    create_parser.add_argument("--username", required=True, help="Benutzername")
    create_parser.add_argument("--password", required=True, help="Passwort")
    create_parser.add_argument("--admin", action="store_true", help="Setzt den Benutzer als Admin")
    
    # list command
    list_parser = subparsers.add_parser("list", help="Listet alle Benutzer auf")
    
    # delete command
    delete_parser = subparsers.add_parser("delete", help="Löscht einen Benutzer")
    delete_parser.add_argument("--username", required=True, help="Benutzername des zu löschenden Benutzers")
    
    # update-password command
    update_parser = subparsers.add_parser("update-password", help="Ändert das Passwort eines Benutzers")
    update_parser.add_argument("--username", required=True, help="Benutzername")
    update_parser.add_argument("--password", required=True, help="Neues Passwort")
    
    args = parser.parse_args()
    
    # Initialisiere KnowledgeBase und UserManager
    kb = KnowledgeBase()
    user_manager = UserManager(kb)
    
    if args.command == "create":
        try:
            user = user_manager.create_user(args.username, args.password, args.admin)
            logger.info(f"Benutzer '{args.username}' erfolgreich erstellt. Admin: {args.admin}")
        except ValueError as e:
            logger.error(str(e))
            exit(1)
    
    elif args.command == "list":
        users = user_manager.list_users()
        if users:
            print("\nBenutzerliste:")
            print("-" * 60)
            print(f"{'Benutzername':<20} {'Admin':<10} {'Erstellt am':<25}")
            print("-" * 60)
            for user in users:
                is_admin = "Ja" if user["is_admin"] else "Nein"
                print(f"{user['username']:<20} {is_admin:<10} {user['created_at']:<25}")
            print("-" * 60)
            print(f"Gesamtanzahl: {len(users)} Benutzer")
        else:
            logger.info("Keine Benutzer gefunden.")
    
    elif args.command == "delete":
        success = user_manager.delete_user(args.username)
        if success:
            logger.info(f"Benutzer '{args.username}' erfolgreich gelöscht.")
        else:
            logger.error(f"Benutzer '{args.username}' konnte nicht gelöscht werden.")
            exit(1)
    
    elif args.command == "update-password":
        success = user_manager.update_password(args.username, args.password)
        if success:
            logger.info(f"Passwort für Benutzer '{args.username}' erfolgreich geändert.")
        else:
            logger.error(f"Passwort für Benutzer '{args.username}' konnte nicht geändert werden.")
            exit(1)

if __name__ == "__main__":
    main()