# src/core/user_manager.py
"""
user_manager.py - Benutzerverwaltung für Mindestentinel

Diese Datei implementiert die Benutzerverwaltung für das System.
Es ermöglicht das Erstellen, Lesen, Aktualisieren und Löschen von Benutzern.
"""

import logging
import os
import json
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger("mindestentinel.user_manager")

class UserManager:
    """
    Verwaltet die Benutzer für das System.
    
    Lädt, speichert und verwaltet Benutzer und ihre Metadaten.
    """
    
    def __init__(self, knowledge_base):
        """
        Initialisiert den UserManager.
        
        Args:
            knowledge_base: Die Wissensdatenbank
        """
        self.kb = knowledge_base
        
        # Initialisiere die Benutzertabelle
        self._initialize_user_table()
        
        logger.info("UserManager initialisiert.")
    
    def _initialize_user_table(self):
        """Initialisiert die Benutzertabelle in der Wissensdatenbank."""
        try:
            # Erstelle die Benutzertabelle, falls nicht vorhanden
            self.kb.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    last_login REAL,
                    enabled BOOLEAN NOT NULL DEFAULT 1
                )
            """)
            logger.debug("Benutzertabelle initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Benutzertabelle: {str(e)}", exc_info=True)
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> bool:
        """
        Erstellt einen neuen Benutzer.
        
        Args:
            username: Der Benutzername
            password: Das Passwort
            is_admin: Gibt an, ob der Benutzer Administrator-Rechte haben soll
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            # Prüfe, ob der Benutzer bereits existiert
            if self.user_exists(username):
                logger.warning(f"Benutzer '{username}' existiert bereits.")
                return False
            
            # Hash das Passwort (in einer echten Implementierung)
            password_hash = self._hash_password(password)
            
            # Füge den Benutzer hinzu
            self.kb.execute(
                "INSERT INTO users (username, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?)",
                (username, password_hash, is_admin, time.time())
            )
            
            logger.info(f"Benutzer '{username}' erstellt. {'(Admin)' if is_admin else ''}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Benutzers: {str(e)}", exc_info=True)
            return False
    
    def _hash_password(self, password: str) -> str:
        """
        Hashed ein Passwort.
        
        Args:
            password: Das Passwort
            
        Returns:
            str: Der Passwort-Hash
        """
        # In einer echten Implementierung würden Sie hier ein sicheres Hashing verwenden
        # Für das Beispiel geben wir einfach den Rohpasswort-Hash zurück
        return password  # NICHT FÜR PRODUKTION - NUR FÜR BEISPIELE
    
    def user_exists(self, username: str) -> bool:
        """
        Prüft, ob ein Benutzer existiert.
        
        Args:
            username: Der Benutzername
            
        Returns:
            bool: True, wenn der Benutzer existiert, sonst False
        """
        try:
            result = self.kb.select(
                "SELECT COUNT(*) FROM users WHERE username = ?",
                (username,)
            )
            return result[0][0] > 0
        except Exception as e:
            logger.error(f"Fehler bei der Überprüfung der Benutzerexistenz: {str(e)}", exc_info=True)
            return False
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Gibt einen Benutzer zurück.
        
        Args:
            username: Der Benutzername
            
        Returns:
            Optional[Dict[str, Any]]: Der Benutzer, falls gefunden, sonst None
        """
        try:
            result = self.kb.select(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            
            if result:
                user_data = result[0]
                return {
                    "id": user_data[0],
                    "username": user_data[1],
                    "is_admin": bool(user_data[2]),
                    "created_at": user_data[3],
                    "last_login": user_data[4],
                    "enabled": bool(user_data[5])
                }
            else:
                logger.warning(f"Benutzer '{username}' nicht gefunden.")
                return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Benutzers: {str(e)}", exc_info=True)
            return None
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """
        Aktualisiert einen Benutzer.
        
        Args:
            username: Der Benutzername
            updates: Die zu aktualisierenden Felder
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            # Erstelle die SET-Klausel
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values())
            values.append(username)
            
            # Führe die Aktualisierung durch
            self.kb.execute(
                f"UPDATE users SET {set_clause} WHERE username = ?",
                tuple(values)
            )
            
            logger.info(f"Benutzer '{username}' aktualisiert.")
            return True
        except Exception as e:
            logger.error(f"Fehler bei der Aktualisierung des Benutzers: {str(e)}", exc_info=True)
            return False
    
    def delete_user(self, username: str) -> bool:
        """
        Löscht einen Benutzer.
        
        Args:
            username: Der Benutzername
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            # Prüfe, ob der Benutzer existiert
            if not self.user_exists(username):
                logger.warning(f"Benutzer '{username}' existiert nicht.")
                return False
            
            # Lösche den Benutzer
            self.kb.execute(
                "DELETE FROM users WHERE username = ?",
                (username,)
            )
            
            logger.info(f"Benutzer '{username}' gelöscht.")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Benutzers: {str(e)}", exc_info=True)
            return False
    
    def list_users(self) -> List[Dict[str, Any]]:
        """
        Listet alle Benutzer auf.
        
        Returns:
            List[Dict[str, Any]]: Liste der Benutzer
        """
        try:
            results = self.kb.select("SELECT * FROM users")
            
            users = []
            for user_data in results:
                users.append({
                    "id": user_data[0],
                    "username": user_data[1],
                    "is_admin": bool(user_data[2]),
                    "created_at": user_data[3],
                    "last_login": user_data[4],
                    "enabled": bool(user_data[5])
                })
            
            return users
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Benutzer: {str(e)}", exc_info=True)
            return []