# src/core/auth_manager.py
"""
auth_manager.py - Authentifizierungs-Management für Mindestentinel

Diese Datei implementiert das Authentifizierungs-Management-System.
"""

import logging
import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Dict, Any, Optional

logger = logging.getLogger("mindestentinel.auth_manager")


class AuthManager:
    """Verwaltet die Authentifizierung und Autorisierung im System"""

    def __init__(self, knowledge_base=None, user_manager=None):
        """Initialisiert den AuthManager

        Args:
            knowledge_base: Wissensdatenbank-Instanz
            user_manager: UserManager-Instanz
        """
        self.kb = knowledge_base
        self.user_manager = user_manager
        self.active_tokens = set()

        # Generiere oder lade den SECRET_KEY
        self.secret_key = self._get_secret_key()
        self.algorithm = "HS256"

        logger.info("AuthManager initialisiert")
        logger.info(f"SECRET_KEY: {self.secret_key[:10]}... (NICHT FÜR PRODUKTION)")

    def _get_secret_key(self) -> str:
        """Holt den SECRET_KEY aus der Umgebung oder generiert einen neuen"""
        secret_key = os.getenv("MIND_JWT_SECRET")
        if secret_key:
            logger.info("Verwende MIND_JWT_SECRET aus Umgebungsvariable")
            return secret_key

        # Generiere einen sicheren Schlüssel
        import secrets
        secret_key = secrets.token_urlsafe(32)
        logger.warning("MIND_JWT_SECRET nicht gesetzt. Verwende generierten Schlüssel (NICHT FÜR PRODUKTION)")
        logger.info(f"Generierter SECRET_KEY: {secret_key[:10]}...")

        return secret_key

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authentifiziert einen Benutzer

        Args:
            username: Benutzername
            password: Passwort

        Returns:
            Dict mit Benutzerinformationen bei Erfolg, sonst None
        """
        logger.debug(f"Authentifiziere Benutzer: {username}")

        if not self.user_manager:
            logger.error("UserManager nicht verfügbar")
            return None

        user = self.user_manager.get_user(username)
        if not user:
            logger.warning(f"Benutzer nicht gefunden: {username}")
            return None

        # In einer echten Implementierung würde hier das Passwort geprüft
        # Für das Beispiel verwenden wir ein festes Passwort
        if password == "SicheresNeuesPasswort123!":
            logger.info(f"Benutzer erfolgreich authentifiziert: {username}")
            return {
                "username": username,
                "is_admin": user.get("is_admin", False)
            }

        logger.warning(f"Falsches Passwort für Benutzer: {username}")
        return None

    def create_access_token(self, username: str, is_admin: bool = False) -> str:
        """Erstellt ein JWT-Zugriffstoken

        Args:
            username: Benutzername
            is_admin: Gibt an, ob der Benutzer Administratorrechte hat

        Returns:
            str: Das generierte Token
        """
        logger.debug(f"Erstelle Token für Benutzer: {username}")

        # Setze Ablaufzeit auf 30 Minuten
        expire = datetime.utcnow() + timedelta(minutes=30)

        # Erstelle den Token-Inhalt
        to_encode = {
            "sub": username,
            "is_admin": is_admin,
            "exp": expire
        }

        # Signiere den Token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        # Speichere das Token in der aktiven Liste
        self.active_tokens.add(encoded_jwt)

        logger.debug(f"Token erstellt für {username}")
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifiziert ein Token und gibt Benutzerinformationen zurück

        Args:
            token: Das zu verifizierende Token

        Returns:
            Dict mit Benutzerinformationen

        Raises:
            HTTPException: Bei ungültigem Token
        """
        logger.debug("Verifiziere Token")

        try:
            # Überprüfe, ob das Token aktiv ist
            if token not in self.active_tokens:
                logger.warning("Token nicht in aktiven Tokens gefunden")
                raise HTTPException(
                    status_code=401,
                    detail="Token ist ungültig oder abgelaufen"
                )

            # Decode das Token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Überprüfe Ablaufzeit
            if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                logger.warning("Token ist abgelaufen")
                self.active_tokens.discard(token)
                raise HTTPException(
                    status_code=401,
                    detail="Token ist abgelaufen"
                )

            logger.debug("Token erfolgreich verifiziert")
            return {
                "sub": payload["sub"],
                "is_admin": payload["is_admin"],
                "exp": payload["exp"]
            }
        except jwt.InvalidTokenError:
            logger.error("Ungültiges Token", exc_info=True)
            self.active_tokens.discard(token)
            raise HTTPException(
                status_code=401,
                detail="Token ist ungültig"
            )
        except Exception as e:
            logger.error(f"Fehler bei der Token-Verifizierung: {str(e)}", exc_info=True)
            self.active_tokens.discard(token)
            raise HTTPException(
                status_code=401,
                detail="Token-Verifizierungsfehler"
            )

    def get_current_user(self, token: str) -> Dict[str, Any]:
        """Holt den aktuellen Benutzer aus dem Token

        Args:
            token: Das Token

        Returns:
            Dict mit Benutzerinformationen

        Raises:
            HTTPException: Bei ungültigem Token
        """
        return self.verify_token(token)

    def logout(self, token: str) -> None:
        """Meldet einen Benutzer ab, indem das Token deaktiviert wird

        Args:
            token: Das Token, das deaktiviert werden soll
        """
        logger.info("Benutzer meldet sich ab")
        self.active_tokens.discard(token)
