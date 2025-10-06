# src/core/user_manager.py
"""
user_manager.py - Verwaltet Benutzer für Mindestentinel

Diese Datei implementiert die Benutzerverwaltung für das System.
"""

import os
import logging
import bcrypt
import secrets
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import sys

from src.core.knowledge_base import KnowledgeBase
from src.core.passwords import is_strong_password

logger = logging.getLogger("mindestentinel.user_manager")

class UserManager:
    """Verwaltet Benutzerkonten"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """Initialisiert den Benutzermanager
        
        Args:
            knowledge_base: Die Wissensdatenbank
        """
        self.kb = knowledge_base
        logger.info("UserManager initialisiert.")
        
        # Stelle sicher, dass die Benutzertabelle existiert
        self._create_user_table_if_not_exists()
    
    def _create_user_table_if_not_exists(self):
        """Erstellt die Benutzertabelle, falls sie nicht existiert"""
        try:
            self.kb.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Benutzertabelle überprüft/erstellt.")
        except Exception as e:
            logger.error(f"Fehler bei der Erstellung der Benutzertabelle: {str(e)}", exc_info=True)
            raise
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> bool:
        """Erstellt einen neuen Benutzer
        
        Args:
            username: Benutzername
            password: Passwort
            is_admin: Gibt an, ob der Benutzer Administratorrechte hat
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info(f"Versuche, Benutzer '{username}' zu erstellen (Admin: {is_admin})")
        
        try:
            # Überprüfe Benutzername
            if not username or len(username) < 3:
                logger.error("Benutzername muss mindestens 3 Zeichen lang sein")
                return False
            
            # Überprüfe Passwortsicherheit
            password_check = is_strong_password(password)
            if password_check is not True:
                logger.error(f"Passwortsicherheitsfehler: {password_check}")
                return False
            
            # Prüfe, ob Benutzer bereits existiert
            if self.user_exists(username):
                logger.warning(f"Benutzer '{username}' existiert bereits")
                return False
            
            # Hash das Passwort
            hashed_password = self._hash_password(password)
            
            # Füge Benutzer zur Datenbank hinzu
            self.kb.execute(
                "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                (username, hashed_password, is_admin)
            )
            
            logger.info(f"Benutzer '{username}' erfolgreich erstellt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Benutzererstellung: {str(e)}", exc_info=True)
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash ein Passwort mit bcrypt
        
        Args:
            password: Klartext-Passwort
            
        Returns:
            str: Gehashtes Passwort
        """
        try:
            # Generiere einen Salt und hash das Passwort
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Fehler beim Hashen des Passworts: {str(e)}", exc_info=True)
            # Fallback: Speichere als Klartext (NICHT EMPFOHLEN, nur für Notfälle)
            return password
    
    def verify_password(self, username: str, password: str) -> bool:
        """Überprüft ein Passwort gegen den gespeicherten Hash
        
        Args:
            username: Benutzername
            password: Klartext-Passwort
            
        Returns:
            bool: True, wenn Passwort korrekt ist
        """
        try:
            user = self.get_user(username)
            if not user:
                logger.warning(f"Benutzer '{username}' nicht gefunden")
                return False
            
            # Extrahiere das gespeicherte Passwort
            stored_password = user['password']
            
            # Prüfe, ob das Passwort bereits gehasht ist
            if stored_password.startswith('$2b$') or stored_password.startswith('$2a$') or stored_password.startswith('$2y$'):
                # Korrektes bcrypt-Format
                try:
                    return bcrypt.checkpw(
                        password.encode('utf-8'),
                        stored_password.encode('utf-8')
                    )
                except Exception as e:
                    logger.warning(f"bcrypt-Überprüfung fehlgeschlagen: {str(e)}")
                    # Versuche es mit direkter String-Überprüfung
                    return password == stored_password
            else:
                # Kein bcrypt-Format - wahrscheinlich Klartext-Passwort
                logger.warning("Gespeichertes Passwort hat kein bcrypt-Format. Verwende Klartext-Überprüfung.")
                return password == stored_password
                
        except Exception as e:
            logger.error(f"Fehler bei der Passwortüberprüfung: {str(e)}", exc_info=True)
            return False
    
    def update_password(self, username: str, password: str) -> bool:
        """Aktualisiert das Passwort eines Benutzers
        
        Args:
            username: Benutzername
            password: Neues Passwort
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info(f"Versuche, Passwort für Benutzer '{username}' zu aktualisieren")
        
        try:
            # Überprüfe Passwortsicherheit
            password_check = is_strong_password(password)
            if password_check is not True:
                logger.error(f"Passwortsicherheitsfehler: {password_check}")
                return False
            
            # Hash das neue Passwort
            hashed_password = self._hash_password(password)
            
            # Aktualisiere das Passwort in der Datenbank
            result = self.kb.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (hashed_password, username)
            )
            
            if result > 0:
                logger.info(f"Passwort für Benutzer '{username}' erfolgreich geändert")
                return True
            else:
                logger.warning(f"Benutzer '{username}' nicht gefunden")
                return False
                
        except Exception as e:
            logger.error(f"Fehler bei der Passwortaktualisierung: {str(e)}", exc_info=True)
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Holt einen Benutzer aus der Datenbank
        
        Args:
            username: Benutzername
            
        Returns:
            Optional[Dict]: Benutzerdaten bei Erfolg, sonst None
        """
        try:
            result = self.kb.query(
                "SELECT username, password, is_admin, created_at FROM users WHERE username = ?",
                (username,)
            )
            
            if result and len(result) > 0:
                user = result[0]
                return {
                    'username': user[0],
                    'password': user[1],
                    'is_admin': user[2],
                    'created_at': user[3]
                }
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Benutzerabfrage: {str(e)}", exc_info=True)
            return None
    
    def user_exists(self, username: str) -> bool:
        """Prüft, ob ein Benutzer existiert
        
        Args:
            username: Benutzername
            
        Returns:
            bool: True, wenn Benutzer existiert
        """
        try:
            result = self.kb.query(
                "SELECT 1 FROM users WHERE username = ? LIMIT 1",
                (username,)
            )
            return len(result) > 0
            
        except Exception as e:
            logger.error(f"Fehler bei der Überprüfung der Benutzerexistenz: {str(e)}", exc_info=True)
            return False
    
    def list_users(self) -> List[Dict]:
        """Listet alle Benutzer auf
        
        Returns:
            List[Dict]: Liste aller Benutzer
        """
        try:
            result = self.kb.query(
                "SELECT username, is_admin, created_at FROM users"
            )
            
            users = []
            for row in result:
                users.append({
                    'username': row[0],
                    'is_admin': row[1],
                    'created_at': row[2]
                })
            
            logger.info(f"{len(users)} Benutzer gefunden")
            return users
            
        except Exception as e:
            logger.error(f"Fehler bei der Benutzerauflistung: {str(e)}", exc_info=True)
            return []
    
    def delete_user(self, username: str) -> bool:
        """Löscht einen Benutzer
        
        Args:
            username: Benutzername
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info(f"Versuche, Benutzer '{username}' zu löschen")
        
        try:
            # Prüfe, ob Benutzer existiert
            if not self.user_exists(username):
                logger.warning(f"Benutzer '{username}' nicht gefunden")
                return False
            
            # Lösche Benutzer
            result = self.kb.execute(
                "DELETE FROM users WHERE username = ?",
                (username,)
            )
            
            if result > 0:
                logger.info(f"Benutzer '{username}' erfolgreich gelöscht")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Benutzers: {str(e)}", exc_info=True)
            return False
    
    def set_admin_status(self, username: str, is_admin: bool) -> bool:
        """Setzt den Admin-Status eines Benutzers
        
        Args:
            username: Benutzername
            is_admin: Neuer Admin-Status
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        logger.info(f"Versuche, Admin-Status für '{username}' auf {is_admin} zu setzen")
        
        try:
            # Prüfe, ob Benutzer existiert
            if not self.user_exists(username):
                logger.warning(f"Benutzer '{username}' nicht gefunden")
                return False
            
            # Aktualisiere den Admin-Status
            result = self.kb.execute(
                "UPDATE users SET is_admin = ? WHERE username = ?",
                (is_admin, username)
            )
            
            if result > 0:
                logger.info(f"Admin-Status für '{username}' erfolgreich geändert")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Fehler bei der Änderung des Admin-Status: {str(e)}", exc_info=True)
            return False
    
    def fix_password_hashes(self):
        """Behebt Passwort-Hash-Probleme für alle Benutzer"""
        logger.info("Behebe Passwort-Hash-Probleme für alle Benutzer...")
        
        try:
            users = self.list_users()
            
            for user in users:
                username = user['username']
                current_password = self.get_user(username)['password']
                
                # Prüfe, ob das Passwort bereits gehasht ist
                if not (current_password.startswith('$2b$') or 
                        current_password.startswith('$2a$') or 
                        current_password.startswith('$2y$')):
                    
                    logger.warning(f"Benutzer '{username}' hat kein gehashtes Passwort. Hash wird neu erstellt.")
                    
                    # Lösung: Setze ein temporäres Passwort
                    temp_password = "TempPass123!" + secrets.token_hex(4)
                    self.update_password(username, temp_password)
                    
                    logger.warning(f"Benutzer '{username}' wurde ein temporäres Passwort zugewiesen: {temp_password}")
        
        except Exception as e:
            logger.error(f"Fehler bei der Passwort-Hash-Korrektur: {str(e)}", exc_info=True)

def handle_admin_commands(args: List[str]):
    """Verarbeitet Admin-Befehle für Benutzermanagement (Top-Level-Funktion)"""
    # Bestimme das Projekt-Root absolut
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # WICHTIG: Verwende denselben Datenbankpfad wie der Server!
    db_path = os.path.join(project_root, "data", "knowledge", "knowledge.db")
    
    # Initialisiere KnowledgeBase mit dem KORREKTEN Datenbankpfad
    kb = KnowledgeBase(db_path=db_path)
    um = UserManager(kb)
    
    # Verarbeite den Befehl
    if len(args) < 1:
        print("Bitte geben Sie einen Unterbefehl an (create, list, delete, update-password)")
        return False
    
    # Prüfe, ob das erste Argument "users" ist
    if args[0] == "users":
        # Wenn ja, dann ist der eigentliche Befehl das zweite Argument
        if len(args) < 2:
            print("Bitte geben Sie einen Unterbefehl an (create, list, delete, update-password)")
            return False
        command = args[1]
        # Die restlichen Argumente sind die Parameter
        command_args = args[2:]
    else:
        # Wenn nicht, dann ist das erste Argument der Befehl
        command = args[0]
        command_args = args[1:]
    
    # Verarbeite den eigentlichen Befehl
    if command == "create":
        if len(command_args) < 3:
            print("Verwendung: admin users create --username <name> --password <pass> [--admin]")
            return False
        
        username = None
        password = None
        is_admin = False
        
        i = 0
        while i < len(command_args):
            if command_args[i] == "--username" and i+1 < len(command_args):
                username = command_args[i+1]
                i += 2
            elif command_args[i] == "--password" and i+1 < len(command_args):
                password = command_args[i+1]
                i += 2
            elif command_args[i] == "--admin":
                is_admin = True
                i += 1
            else:
                i += 1
        
        if not username or not password:
            print("Benutzername und Passwort sind erforderlich")
            return False
        
        success = um.create_user(username, password, is_admin)
        if success:
            print(f"Benutzer '{username}' erfolgreich erstellt")
            return True
        else:
            print(f"Fehler beim Erstellen des Benutzers '{username}'")
            return False
    
    elif command == "list":
        users = um.list_users()
        
        print("Benutzerliste:")
        print("- Benutzername\tAdmin\tErstellt am")
        for user in users:
            print(f"- {user['username']}\t{'Ja' if user['is_admin'] else 'Nein'}\t{user['created_at']}")
        print(f"- Gesamtanzahl: {len(users)} Benutzer")
        return True
    
    elif command == "delete":
        if len(command_args) < 2:
            print("Verwendung: admin users delete --username <name>")
            return False
        
        username = None
        i = 0
        while i < len(command_args):
            if command_args[i] == "--username" and i+1 < len(command_args):
                username = command_args[i+1]
                i += 2
            else:
                i += 1
        
        if not username:
            print("Benutzername ist erforderlich")
            return False
        
        success = um.delete_user(username)
        if success:
            print(f"Benutzer '{username}' erfolgreich gelöscht")
            return True
        else:
            print(f"Fehler beim Löschen des Benutzers '{username}'")
            return False
    
    elif command == "update-password":
        if len(command_args) < 3:
            print("Verwendung: admin users update-password --username <name> --password <pass>")
            return False
        
        username = None
        password = None
        i = 0
        while i < len(command_args):
            if command_args[i] == "--username" and i+1 < len(command_args):
                username = command_args[i+1]
                i += 2
            elif command_args[i] == "--password" and i+1 < len(command_args):
                password = command_args[i+1]
                i += 2
            else:
                i += 1
        
        if not username or not password:
            print("Benutzername und Passwort sind erforderlich")
            return False
        
        success = um.update_password(username, password)
        if success:
            print(f"Passwort für Benutzer '{username}' erfolgreich geändert")
            return True
        else:
            print(f"Fehler beim Ändern des Passworts für Benutzer '{username}'")
            return False
    
    else:
        print(f"Unbekannter Befehl: {command}")
        print("Verfügbare Befehle: create, list, delete, update-password")
        return False