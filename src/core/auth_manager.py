# src/core/auth_manager.py
"""
auth_manager.py - Authentifizierungs-Manager für Mindestentinel

Diese Datei implementiert das Authentifizierungssystem für das System.
Es ermöglicht die Verwaltung von Benutzern, Rollen und Berechtigungen.
"""

import logging
import os
import json
import time
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import pyotp

logger = logging.getLogger("mindestentinel.auth_manager")

class AuthManager:
    """
    Verwaltet die Authentifizierung und Autorisierung für das System.
    
    Lädt, speichert und verwaltet Benutzer, Rollen und Berechtigungen.
    """
    
    def __init__(self, kb, users_file: str = "data/users/users.json", key_file: str = "data/users/encryption.key"):
        """
        Initialisiert den AuthManager.
        
        Args:
            kb: Die Wissensdatenbank
            users_file: Pfad zur Benutzerdatei
            key_file: Pfad zur Verschlüsselungsschlüsseldatei
        """
        self.kb = kb
        self.users_file = users_file
        self.key_file = key_file
        self.users = {}
        
        # Erstelle Benutzer-Verzeichnis, falls nicht vorhanden
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        
        # Lade oder erstelle den Verschlüsselungsschlüssel
        self.encryption_key = self._load_or_create_encryption_key()
        
        # Lade Benutzer
        self.load_users()
        
        logger.info("AuthManager initialisiert.")
    
    def _load_or_create_encryption_key(self) -> bytes:
        """
        Lädt den Verschlüsselungsschlüssel oder erstellt einen neuen.
        
        Returns:
            bytes: Der Verschlüsselungsschlüssel
        """
        if os.path.exists(self.key_file):
            # Lade den vorhandenen Schlüssel
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Erstelle einen neuen Schlüssel
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _encrypt(self, data: str) -> str:
        """
        Verschlüsselt Daten.
        
        Args:
            data: Die zu verschlüsselnden Daten
            
        Returns:
            str: Die verschlüsselten Daten
        """
        f = Fernet(self.encryption_key)
        return f.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """
        Entschlüsselt Daten.
        
        Args:
            encrypted_data: Die verschlüsselten Daten
            
        Returns:
            str: Die entschlüsselten Daten
        """
        f = Fernet(self.encryption_key)
        return f.decrypt(encrypted_data.encode()).decode()
    
    def load_users(self):
        """Lädt die Benutzer aus der Benutzerdatei."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                
                # Entschlüssle die sensiblen Daten
                for username, user_data in users_data.items():
                    if "password_hash" in user_data:
                        user_data["password_hash"] = self._decrypt(user_data["password_hash"])
                    if "totp_secret" in user_data:
                        user_data["totp_secret"] = self._decrypt(user_data["totp_secret"])
                    if "backup_codes" in user_data:
                        user_data["backup_codes"] = [self._decrypt(code) for code in user_data["backup_codes"]]
                
                self.users = users_data
                logger.info(f"{len(self.users)} Benutzer geladen.")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Benutzer: {str(e)}", exc_info=True)
                self.users = {}
        else:
            # Erstelle eine neue Benutzerdatei
            self.users = {}
            self.save_users()
    
    def save_users(self):
        """Speichert die Benutzer in die Benutzerdatei."""
        # Verschlüssele die sensiblen Daten
        users_data = {}
        for username, user_data in self.users.items():
            users_data[username] = user_data.copy()
            if "password_hash" in users_data[username]:
                users_data[username]["password_hash"] = self._encrypt(users_data[username]["password_hash"])
            if "totp_secret" in users_data[username]:
                users_data[username]["totp_secret"] = self._encrypt(users_data[username]["totp_secret"])
            if "backup_codes" in users_data[username]:
                users_data[username]["backup_codes"] = [self._encrypt(code) for code in users_data[username]["backup_codes"]]
        
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
            logger.debug("Benutzer gespeichert.")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Benutzer: {str(e)}", exc_info=True)
    
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
        if username in self.users:
            logger.warning(f"Benutzer '{username}' existiert bereits.")
            return False
        
        # Erstelle ein TOTP-Secret
        totp_secret = pyotp.random_base32()
        
        # Erstelle Backup-Codes
        backup_codes = [secrets.token_hex(8) for _ in range(10)]
        
        # Erstelle den Benutzer
        self.users[username] = {
            "username": username,
            "password_hash": self._hash_password(password),
            "is_admin": is_admin,
            "created_at": time.time(),
            "last_login": None,
            "totp_secret": totp_secret,
            "backup_codes": backup_codes,
            "enabled": True
        }
        
        # Speichere die Benutzer
        self.save_users()
        
        logger.info(f"Benutzer '{username}' erstellt. {'(Admin)' if is_admin else ''}")
        
        # Gib die TOTP-Secret und Backup-Codes zurück
        print(f"\nBenutzer '{username}' erfolgreich erstellt!")
        print(f"TOTP-Secret: {totp_secret}")
        print("Scannen Sie diesen QR-Code mit Ihrer Authenticator-App:")
        print(pyotp.totp.TOTP(totp_secret).provisioning_uri(username, issuer_name="Mindestentinel"))
        print("\nBackup-Codes (speichern Sie diese an einem sicheren Ort):")
        for i, code in enumerate(backup_codes, 1):
            print(f"{i}. {code}")
        
        return True
    
    def _hash_password(self, password: str) -> str:
        """
        Hashed ein Passwort.
        
        Args:
            password: Das Passwort
            
        Returns:
            str: Der Passwort-Hash
        """
        # Erstelle einen Salt
        salt = secrets.token_hex(16)
        
        # Erstelle einen Key Derivation Function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        
        # Erstelle den Hash
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Gib den Hash im Format "salt:hash" zurück
        return f"{salt}:{key.decode()}"
    
    def verify_password(self, username: str, password: str) -> bool:
        """
        Überprüft ein Passwort.
        
        Args:
            username: Der Benutzername
            password: Das Passwort
            
        Returns:
            bool: True, wenn das Passwort korrekt ist, sonst False
        """
        if username not in self.users:
            return False
        
        user = self.users[username]
        salt, stored_hash = user["password_hash"].split(":")
        
        # Erstelle einen Key Derivation Function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
            backend=default_backend()
        )
        
        # Erstelle den Hash des eingegebenen Passworts
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Vergleiche die Hashes
        return secrets.compare_digest(key.decode(), stored_hash)
    
    def verify_totp(self, username: str, totp_code: str) -> bool:
        """
        Überprüft einen TOTP-Code.
        
        Args:
            username: Der Benutzername
            totp_code: Der TOTP-Code
            
        Returns:
            bool: True, wenn der Code korrekt ist, sonst False
        """
        if username not in self.users:
            return False
        
        user = self.users[username]
        totp = pyotp.TOTP(user["totp_secret"])
        return totp.verify(totp_code)
    
    def verify_backup_code(self, username: str, backup_code: str) -> bool:
        """
        Überprüft einen Backup-Code.
        
        Args:
            username: Der Benutzername
            backup_code: Der Backup-Code
            
        Returns:
            bool: True, wenn der Code korrekt ist, sonst False
        """
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # Prüfe, ob der Code in den Backup-Codes enthalten ist
        if backup_code in user["backup_codes"]:
            # Entferne den verwendeten Backup-Code
            user["backup_codes"].remove(backup_code)
            self.save_users()
            return True
        
        return False
    
    def login(self, username: str, password: str, totp_code: Optional[str] = None) -> bool:
        """
        Führt eine Anmeldung durch.
        
        Args:
            username: Der Benutzername
            password: Das Passwort
            totp_code: Der TOTP-Code (optional)
            
        Returns:
            bool: True, wenn die Anmeldung erfolgreich war, sonst False
        """
        # Prüfe, ob der Benutzer existiert
        if username not in self.users:
            logger.warning(f"Anmeldeversuch für nicht existierenden Benutzer '{username}'.")
            return False
        
        user = self.users[username]
        
        # Prüfe, ob der Benutzer aktiviert ist
        if not user["enabled"]:
            logger.warning(f"Anmeldeversuch für deaktivierten Benutzer '{username}'.")
            return False
        
        # Prüfe das Passwort
        if not self.verify_password(username, password):
            logger.warning(f"Falsches Passwort für Benutzer '{username}'.")
            return False
        
        # Prüfe den TOTP-Code, falls erforderlich
        if totp_code:
            if not self.verify_totp(username, totp_code) and not self.verify_backup_code(username, totp_code):
                logger.warning(f"Falscher TOTP-Code für Benutzer '{username}'.")
                return False
        else:
            logger.warning(f"Kein TOTP-Code für Benutzer '{username}' angegeben.")
            return False
        
        # Aktualisiere den letzten Anmeldezeitpunkt
        self.users[username]["last_login"] = time.time()
        self.save_users()
        
        logger.info(f"Benutzer '{username}' erfolgreich angemeldet.")
        return True
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Gibt einen Benutzer zurück.
        
        Args:
            username: Der Benutzername
            
        Returns:
            Optional[Dict[str, Any]]: Der Benutzer, falls gefunden, sonst None
        """
        if username in self.users:
            return self.users[username].copy()
        else:
            logger.warning(f"Benutzer '{username}' nicht gefunden.")
            return None
    
    def is_admin(self, username: str) -> bool:
        """
        Prüft, ob ein Benutzer Administrator-Rechte hat.
        
        Args:
            username: Der Benutzername
            
        Returns:
            bool: True, wenn der Benutzer Administrator-Rechte hat, sonst False
        """
        user = self.get_user(username)
        return user["is_admin"] if user else False
    
    def disable_user(self, username: str) -> bool:
        """
        Deaktiviert einen Benutzer.
        
        Args:
            username: Der Benutzername
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        if username in self.users:
            self.users[username]["enabled"] = False
            self.save_users()
            logger.info(f"Benutzer '{username}' deaktiviert.")
            return True
        else:
            logger.warning(f"Benutzer '{username}' nicht gefunden.")
            return False
    
    def enable_user(self, username: str) -> bool:
        """
        Aktiviert einen Benutzer.
        
        Args:
            username: Der Benutzername
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        if username in self.users:
            self.users[username]["enabled"] = True
            self.save_users()
            logger.info(f"Benutzer '{username}' aktiviert.")
            return True
        else:
            logger.warning(f"Benutzer '{username}' nicht gefunden.")
            return False
    
    def list_users(self) -> List[Dict[str, Any]]:
        """
        Listet alle Benutzer auf.
        
        Returns:
            List[Dict[str, Any]]: Liste der Benutzer
        """
        return [user.copy() for user in self.users.values()]
    
    def generate_api_key(self, username: str) -> Optional[str]:
        """
        Generiert einen API-Schlüssel für einen Benutzer.
        
        Args:
            username: Der Benutzername
            
        Returns:
            Optional[str]: Der API-Schlüssel, falls erfolgreich, sonst None
        """
        if username not in self.users:
            logger.warning(f"Benutzer '{username}' nicht gefunden. Kann keinen API-Schlüssel generieren.")
            return None
        
        # Generiere einen sicheren API-Schlüssel
        api_key = secrets.token_urlsafe(32)
        
        # Speichere den API-Schlüssel im Benutzer
        self.users[username]["api_key"] = self._encrypt(api_key)
        self.save_users()
        
        logger.info(f"API-Schlüssel für Benutzer '{username}' generiert.")
        return api_key
    
    def verify_api_key(self, api_key: str) -> bool:
        """
        Überprüft einen API-Schlüssel.
        
        Args:
            api_key: Der API-Schlüssel
            
        Returns:
            bool: True, wenn der Schlüssel gültig ist, sonst False
        """
        for username, user in self.users.items():
            if "api_key" in user:
                try:
                    decrypted_api_key = self._decrypt(user["api_key"])
                    if secrets.compare_digest(decrypted_api_key, api_key):
                        return True
                except Exception as e:
                    logger.error(f"Fehler bei der API-Schlüssel-Überprüfung: {str(e)}", exc_info=True)
        
        return False