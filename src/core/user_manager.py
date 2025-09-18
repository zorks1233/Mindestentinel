# src/core/user_manager.py
"""
user_manager.py - Benutzerverwaltung für Mindestentinel

Diese Datei implementiert die Benutzerverwaltung für das System.
Es ermöglicht das Erstellen, Aktualisieren und Löschen von Benutzern,
sowie das Setzen von Passwörtern und Admin-Rechten.

Alle Passwörter werden sicher mit bcrypt gehasht gespeichert.
"""

import logging
import datetime
from typing import List, Dict, Any, Optional
from passlib.context import CryptContext
from src.core.knowledge_base import KnowledgeBase

logger = logging.getLogger("mindestentinel.user_manager")

# Passwort-Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager:
    """
    Verwaltet Benutzerkonten für das System.
    
    Alle Passwörter werden sicher gehasht gespeichert.
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        """
        Initialisiert den Benutzermanager.
        
        Args:
            knowledge_base: Die Wissensdatenbank
        """
        self.kb = knowledge_base
        self._init_db()
        logger.info("UserManager initialisiert.")
    
    def _init_db(self):
        """Initialisiert die Benutzertabelle in der Datenbank."""
        try:
            # Erstelle Benutzertabelle, falls nicht vorhanden
            self.kb.query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
            """)
            
            logger.debug("Benutzertabelle initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Benutzertabelle: {str(e)}", exc_info=True)
            raise
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> Dict[str, Any]:
        """
        Erstellt einen neuen Benutzer.
        
        Args:
            username: Der Benutzername
            password: Das Passwort (wird gehasht gespeichert)
            is_admin: Gibt an, ob der Benutzer Admin-Rechte hat
            
        Returns:
            Dict[str, Any]: Die erstellten Benutzerdaten
            
        Raises:
            ValueError: Wenn der Benutzername bereits existiert
        """
        # PRÜFE MIT SELECT, NICHT MIT QUERY - WICHTIGE KORREKTUR
        existing = self.kb.select(
            "SELECT id FROM users WHERE username = ?",
            (username,),
            decrypt_column=None
        )
        
        if existing:
            raise ValueError(f"Benutzer '{username}' existiert bereits")
        
        # Hashe das Passwort
        password_hash = pwd_context.hash(password)
        
        # Erstelle Benutzer
        created_at = datetime.datetime.now().isoformat()
        self.kb.query(
            "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, int(is_admin), created_at)
        )
        
        # Hole den neu erstellten Benutzer
        user = self.kb.select(
            "SELECT id, username, is_admin, created_at FROM users WHERE username = ?",
            (username,),
            decrypt_column=None
        )[0]
        
        logger.info(f"Benutzer '{username}' erstellt. Admin: {is_admin}")
        return user
    
    def update_password(self, username: str, new_password: str) -> bool:
        """
        Aktualisiert das Passwort eines Benutzers.
        
        Args:
            username: Der Benutzername
            new_password: Das neue Passwort
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        logger.info(f"Versuche, Passwort für Benutzer '{username}' zu aktualisieren...")
        
        # PRÜFE MIT SELECT, NICHT MIT QUERY - WICHTIGE KORREKTUR
        existing = self.kb.select(
            "SELECT id FROM users WHERE username = ?",
            (username,),
            decrypt_column=None
        )
        
        if not existing:
            logger.error(f"Benutzer '{username}' existiert nicht")
            return False
        
        # Hashe das neue Passwort
        password_hash = pwd_context.hash(new_password)
        
        # Aktualisiere das Passwort
        result = self.kb.query(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (password_hash, username)
        )
        
        logger.info(f"Anzahl betroffener Zeilen: {result}")
        
        # Wichtig: Bei SQLite gibt rowcount 0 zurück, wenn sich der Wert nicht ändert
        # Wir prüfen daher explizit, ob der Benutzer existiert
        if result >= 0:
            logger.info(f"Passwort für Benutzer '{username}' aktualisiert")
            return True
        else:
            logger.warning(f"Passwort für Benutzer '{username}' konnte nicht aktualisiert werden")
            return False
    
    def set_admin_status(self, username: str, is_admin: bool) -> bool:
        """
        Setzt den Admin-Status eines Benutzers.
        
        Args:
            username: Der Benutzername
            is_admin: Der neue Admin-Status
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        result = self.kb.query(
            "UPDATE users SET is_admin = ? WHERE username = ?",
            (int(is_admin), username)
        )
        
        if result > 0:
            status = "Admin" if is_admin else "kein Admin"
            logger.info(f"Benutzer '{username}' ist jetzt {status}")
            return True
        else:
            logger.warning(f"Admin-Status für Benutzer '{username}' konnte nicht geändert werden")
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authentifiziert einen Benutzer.
        
        Args:
            username: Der Benutzername
            password: Das Passwort
            
        Returns:
            Optional[Dict[str, Any]]: Benutzerdaten, falls erfolgreich, sonst None
        """
        # Hole Benutzer aus der Datenbank
        users = self.kb.select(
            "SELECT id, username, password_hash, is_admin, created_at FROM users WHERE username = ?",
            (username,),
            decrypt_column=None
        )
        
        if not users:
            logger.warning(f"Benutzer '{username}' nicht gefunden")
            return None
            
        user = users[0]
        
        # Überprüfe das Passwort
        if not pwd_context.verify(password, user["password_hash"]):
            logger.warning(f"Falsches Passwort für Benutzer '{username}'")
            return None
        
        # Aktualisiere letzte Anmeldezeit
        self.kb.query(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.datetime.now().isoformat(), user["id"])
        )
        
        return {
            "id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"],
            "created_at": user["created_at"]
        }
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Holt die Benutzerdaten.
        
        Args:
            username: Der Benutzername
            
        Returns:
            Optional[Dict[str, Any]]: Benutzerdaten, falls gefunden, sonst None
        """
        users = self.kb.select(
            "SELECT id, username, is_admin, created_at, last_login FROM users WHERE username = ?",
            (username,),
            decrypt_column=None
        )
        
        return users[0] if users else None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """
        Listet alle Benutzer auf.
        
        Returns:
            List[Dict[str, Any]]: Liste aller Benutzer
        """
        return self.kb.select(
            "SELECT id, username, is_admin, created_at, last_login FROM users ORDER BY created_at DESC",
            decrypt_column=None
        )
    
    def delete_user(self, username: str) -> bool:
        """
        Löscht einen Benutzer.
        
        Args:
            username: Der Benutzername
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        result = self.kb.query(
            "DELETE FROM users WHERE username = ?",
            (username,)
        )
        
        if result > 0:
            logger.info(f"Benutzer '{username}' gelöscht")
            return True
        else:
            logger.warning(f"Benutzer '{username}' konnte nicht gelöscht werden")
            return False