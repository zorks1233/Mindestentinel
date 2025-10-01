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
from typing import Dict, Any, Optional
import pyotp
from src.core.token_utils import create_token, decode_token, JWTError

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
    
    def login(self, username: str, password: str, client_secret: Optional[str] = None, totp_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Authentifiziert einen Benutzer.
        
        Args:
            username: Der Benutzername
            password: Das Passwort
            client_secret: Das Client-Geheimnis (optional)
            totp_code: Der TOTP-Code (optional)
            
        Returns:
            Dict[str, Any]: Ein Dictionary mit dem Token und Benutzerinformationen
        """
        # Hole den Benutzer
        user = self.user_manager.get_user(username)
        if not user:
            logger.warning(f"Benutzer '{username}' nicht gefunden")
            return {"success": False, "message": "Benutzername oder Passwort falsch"}
        
        # Prüfe, ob der Benutzer aktiv ist
        if not user["enabled"]:
            logger.warning(f"Benutzer '{username}' ist deaktiviert")
            return {"success": False, "message": "Benutzerkonto ist deaktiviert"}
        
        # Verifiziere das Passwort
        from src.core.passwords import verify_password
        if not verify_password(password, user["password_hash"]):
            logger.warning(f"Falsches Passwort für Benutzer '{username}'")
            return {"success": False, "message": "Benutzername oder Passwort falsch"}
        
        # Prüfe 2FA, falls erforderlich
        if user["totp_secret"]:
            if not totp_code:
                return {"success": False, "require_2fa": True, "message": "2FA erforderlich"}
            
            # Verifiziere den TOTP-Code
            totp = pyotp.TOTP(user["totp_secret"])
            if not totp.verify(totp_code):
                # Prüfe, ob es ein Backup-Code ist
                if not self.user_manager.verify_2fa_backup_code(username, totp_code):
                    return {"success": False, "message": "Ungültiger 2FA-Code"}
        
        # Aktualisiere den letzten Login-Zeitpunkt
        self.user_manager.update_user(username, {"last_login": time.time()})
        
        # Erstelle ein Token
        payload = {
            "sub": username,
            "username": username,
            "is_admin": user["is_admin"]
        }
        
        try:
            # Erstelle ein Token mit Refresh-Token
            from src.config import MIND_JWT_SECRET, MIND_JWT_ALG, MIND_JWT_EXP
            access_token = create_token(
                payload, 
                MIND_JWT_SECRET, 
                MIND_JWT_ALG,
                MIND_JWT_EXP
            )
            
            tokens = {
                "access_token": access_token,
                "token_type": "bearer",
                "username": username,
                "is_admin": user["is_admin"]
            }
            
            logger.info(f"Benutzer '{username}' erfolgreich authentifiziert")
            return {"success": True, **tokens}
        except JWTError as e:
            logger.error(f"Fehler bei der Token-Erstellung: {str(e)}")
            return {"success": False, "message": "Token-Erstellung fehlgeschlagen"}
    
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
    
    def generate_api_key(self, username: str, description: str = "") -> str:
        """
        Generiert einen API-Schlüssel für einen Benutzer.
        
        Args:
            username: Der Benutzername
            description: Beschreibung des API-Schlüssels
            
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
                "INSERT INTO api_keys (user_id, api_key, created_at, description) VALUES (?, ?, ?, ?)",
                (user["id"], api_key, time.time(), description)
            )
            logger.info(f"API-Schlüssel für Benutzer '{username}' generiert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des API-Schlüssels: {str(e)}", exc_info=True)
        
        return api_key
    
    def setup_2fa(self, username: str) -> Dict[str, Any]:
        """
        Richtet 2FA für einen Benutzer ein.
        
        Args:
            username: Der Benutzername
            
        Returns:
            Dict[str, Any]: TOTP-Secret, QR-Code-URL und Backup-Codes
        """
        # Generiere ein TOTP-Secret
        secret = pyotp.random_base32()
        
        # Generiere Backup-Codes
        backup_codes = [secrets.token_hex(6) for _ in range(10)]
        
        # Speichere das Secret und die Backup-Codes
        if self.user_manager.set_2fa_secret(username, secret, backup_codes):
            # Erstelle eine TOTP-Instanz
            totp = pyotp.TOTP(secret)
            
            # Generiere die QR-Code-URL
            provisioning_uri = totp.provisioning_uri(
                name=username,
                issuer_name="Mindestentinel"
            )
            
            return {
                "secret": secret,
                "qr_code": provisioning_uri,
                "backup_codes": backup_codes
            }
        
        return {"error": "Fehler bei der 2FA-Einrichtung"}
    
    def disable_2fa(self, username: str) -> bool:
        """
        Deaktiviert 2FA für einen Benutzer.
        
        Args:
            username: Der Benutzername
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        return self.user_manager.set_2fa_secret(username, "", [])