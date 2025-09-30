# src/core/auth_manager.py
"""
auth_manager.py - Authentifizierungs-Manager für Mindestentinel

Diese Datei implementiert die Authentifizierung für das System.
Es ermöglicht die Benutzerauthentifizierung und Token-Verwaltung.
"""

import logging
import os
import time
import hashlib
import secrets
import bcrypt  # Stellen Sie sicher: pip install bcrypt
from typing import Dict, Any, Optional

logger = logging.getLogger("mindestentinel.auth_manager")

class AuthManager:
    """
    Verwaltet die Authentifizierung für das System.
    
    Lädt, speichert und verwaltet Benutzer und ihre Authentifizierungsdaten.
    """
    
    def __init__(self, knowledge_base, user_manager=None):
        """
        Initialisiert den AuthManager.
        
        Args:
            knowledge_base: Die Wissensdatenbank
            user_manager: Der UserManager (optional)
        """
        self.kb = knowledge_base
        self.user_manager = user_manager
        
        # Initialisiere die API-Schlüssel-Tabelle
        self._initialize_api_keys_table()
        
        logger.info("AuthManager initialisiert.")
    
    def _initialize_api_keys_table(self):
        """Initialisiert die API-Schlüssel-Tabelle in der Wissensdatenbank."""
        try:
            # Erstelle die API-Schlüssel-Tabelle, falls nicht vorhanden
            self.kb.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    created_at REAL NOT NULL,
                    last_used REAL,
                    expires_at REAL,
                    description TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            logger.debug("API-Schlüssel-Tabelle initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der API-Schlüssel-Tabelle: {str(e)}", exc_info=True)
    
    def login(self, username: str, password: str, client_secret: Optional[str] = None) -> bool:
        """
        Authentifiziert einen Benutzer.
        
        Args:
            username: Der Benutzername
            password: Das Passwort
            client_secret: Das Client-Geheimnis (optional)
            
        Returns:
            bool: True, wenn die Authentifizierung erfolgreich war, sonst False
        """
        # Hole den Benutzer
        user = self.user_manager.get_user(username)
        if not user:
            logger.warning(f"Benutzer '{username}' nicht gefunden")
            return False
        
        # Prüfe, ob der Benutzer aktiv ist
        if not user["enabled"]:
            logger.warning(f"Benutzer '{username}' ist deaktiviert")
            return False
        
        # Verifiziere das Passwort MIT BCRYPT
        if not self._verify_password(password, user["password_hash"]):
            logger.warning(f"Falsches Passwort für Benutzer '{username}'")
            return False
        
        # Aktualisiere den letzten Login-Zeitpunkt
        self.user_manager.update_user(username, {"last_login": time.time()})
        
        logger.info(f"Benutzer '{username}' erfolgreich authentifiziert")
        return True
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verifiziert ein Passwort gegen einen gespeicherten Hash MIT BCRYPT.
        
        Args:
            password: Das zu prüfende Passwort
            stored_hash: Der gespeicherte Hash
            
        Returns:
            bool: True, wenn das Passwort korrekt ist, sonst False
        """
        try:
            # Konvertiere den gespeicherten Hash in Bytes
            stored_hash_bytes = stored_hash.encode('utf-8')
            
            # Verifiziere das Passwort MIT BCRYPT
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes)
        except Exception as e:
            logger.error(f"Fehler bei der Passwortverifikation: {str(e)}", exc_info=True)
            return False
    
    def generate_api_key(self, username: str) -> str:
        """
        Generiert einen API-Schlüssel für einen Benutzer.
        
        Args:
            username: Der Benutzername
            
        Returns:
            str: Der API-Schlüssel
        """
        # Hole den Benutzer
        user = self.user_manager.get_user(username)
        if not user:
            logger.warning(f"Benutzer '{username}' nicht gefunden für API-Schlüssel-Generierung")
            return ""
        
        # Generiere einen sicheren API-Schlüssel
        api_key = secrets.token_urlsafe(32)
        
        # Speichere den API-Schlüssel in der Datenbank
        try:
            self.kb.execute(
                "INSERT INTO api_keys (user_id, api_key, created_at) VALUES (?, ?, ?)",
                (user["id"], api_key, time.time())
            )
            logger.info(f"API-Schlüssel für Benutzer '{username}' generiert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des API-Schlüssels: {str(e)}", exc_info=True)
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Verifiziert einen API-Schlüssel.
        
        Args:
            api_key: Der API-Schlüssel
            
        Returns:
            bool: True, wenn der API-Schlüssel gültig ist, sonst False
        """
        try:
            result = self.kb.select(
                "SELECT COUNT(*) FROM api_keys WHERE api_key = ?",
                (api_key,)
            )
            return len(result) > 0 and result[0][0] > 0
        except Exception as e:
            logger.error(f"Fehler bei der API-Schlüssel-Verifikation: {str(e)}", exc_info=True)
            return False
    
    def get_user_for_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Gibt den Benutzer für einen API-Schlüssel zurück.
        
        Args:
            api_key: Der API-Schlüssel
            
        Returns:
            Optional[Dict[str, Any]]: Der Benutzer, falls gefunden, sonst None
        """
        try:
            result = self.kb.select("""
                SELECT users.* FROM api_keys
                JOIN users ON api_keys.user_id = users.id
                WHERE api_key = ?
            """, (api_key,))
            
            if result:
                user_data = result[0]
                return {
                    "id": user_data[0],
                    "username": user_data[1],
                    "is_admin": bool(user_data[3]),
                    "created_at": user_data[4],
                    "last_login": user_data[5],
                    "enabled": bool(user_data[6])
                }
            return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Benutzers für API-Schlüssel: {str(e)}", exc_info=True)
            return None