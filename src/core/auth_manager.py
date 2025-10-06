# src/core/auth_manager.py
"""
AuthManager - Verwaltet die Authentifizierung und Autorisierung für Mindestentinel

Diese Klasse implementiert:
- JWT-Token-Erstellung und -Verifizierung
- Passwort-Hashing mit bcrypt
- Benutzer-Authentifizierung
- Rollenbasierte Zugriffskontrolle
"""

import os
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import secrets
from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer

# Korrigierter JWT-Import
try:
    import jwt
    from jwt.exceptions import PyJWTError, ExpiredSignatureError
except ImportError:
    # Fallback für ältere PyJWT-Versionen
    import jwt
    PyJWTError = jwt.PyJWTError if hasattr(jwt, 'PyJWTError') else Exception
    ExpiredSignatureError = jwt.ExpiredSignatureError if hasattr(jwt, 'ExpiredSignatureError') else Exception

logger = logging.getLogger("mindestentinel.auth")

# Konfiguration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Sicherer Schlüssel aus Umgebungsvariable oder generieren (nur für Entwicklung)
SECRET_KEY = os.getenv("MIND_JWT_SECRET")
if not SECRET_KEY:
    logger.warning("MIND_JWT_SECRET nicht gesetzt. Verwende generierten Schlüssel (NICHT FÜR PRODUKTION)")
    SECRET_KEY = secrets.token_urlsafe(32)
    logger.info(f"Generierter SECRET_KEY: {SECRET_KEY[:10]}...")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthManager:
    """Verwaltet Authentifizierung und Autorisierung"""
    
    def __init__(self, knowledge_base, user_manager):
        """Initialisiert den AuthManager
        
        Args:
            knowledge_base: Die Wissensdatenbank
            user_manager: UserManager-Instanz
        """
        self.kb = knowledge_base
        self.user_manager = user_manager
        logger.info("AuthManager initialisiert")
    
    def create_access_token(self, username: str, is_admin: bool = False) -> str:
        """Erstellt ein JWT-Zugriffstoken
        
        Args:
            username: Benutzername
            is_admin: Gibt an, ob der Benutzer Administratorrechte hat
            
        Returns:
            str: JWT-Zugriffstoken
        """
        try:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            expire = datetime.utcnow() + expires_delta
            
            to_encode = {
                "sub": username,
                "exp": expire,
                "is_admin": is_admin,
                "token_type": "access"
            }
            
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            logger.info(f"Zugriffstoken erstellt für {username} (Admin: {is_admin})")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Fehler bei der Token-Erstellung: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Token-Erstellung fehlgeschlagen"
            )
    
    def create_refresh_token(self, username: str) -> str:
        """Erstellt ein JWT-Refresh-Token
        
        Args:
            username: Benutzername
            
        Returns:
            str: JWT-Refresh-Token
        """
        try:
            expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            expire = datetime.utcnow() + expires_delta
            
            to_encode = {
                "sub": username,
                "exp": expire,
                "token_type": "refresh"
            }
            
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Fehler bei der Refresh-Token-Erstellung: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Refresh-Token-Erstellung fehlgeschlagen"
            )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Überprüft ein Passwort gegen einen Hash
        
        Args:
            plain_password: Klartext-Passwort
            hashed_password: Gehashtes Passwort
            
        Returns:
            bool: True, wenn Passwort korrekt ist
        """
        try:
            # Stelle sicher, dass hashed_password ein String ist
            if isinstance(hashed_password, bytes):
                hashed_password = hashed_password.decode('utf-8')
            
            # Prüfe, ob das Passwort bereits gehasht ist
            if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$') or hashed_password.startswith('$2y$'):
                # Korrektes bcrypt-Format
                try:
                    return bcrypt.checkpw(
                        plain_password.encode('utf-8'),
                        hashed_password.encode('utf-8')
                    )
                except Exception as e:
                    logger.warning(f"bcrypt-Überprüfung fehlgeschlagen: {str(e)}")
                    # Versuche es mit direkter String-Überprüfung
                    return plain_password == hashed_password
            else:
                # Kein bcrypt-Format - wahrscheinlich Klartext-Passwort
                logger.warning("Gespeichertes Passwort hat kein bcrypt-Format. Verwende Klartext-Überprüfung.")
                return plain_password == hashed_password
                
        except Exception as e:
            logger.error(f"Fehler bei der Passwortüberprüfung: {str(e)}", exc_info=True)
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authentifiziert einen Benutzer
        
        Args:
            username: Benutzername
            password: Passwort
            
        Returns:
            Optional[Dict]: Benutzerdaten bei Erfolg, sonst None
        """
        logger.info(f"Authentifizierungsversuch für Benutzer: {username}")
        
        try:
            # Hole Benutzer aus der Datenbank
            user = self.user_manager.get_user(username)
            
            if not user:
                logger.warning(f"Benutzer '{username}' nicht gefunden")
                return None
                
            # Extrahiere das gespeicherte Passwort
            stored_password = user['password']
            
            # Überprüfe Passwort
            if not self.verify_password(password, stored_password):
                logger.warning(f"Falsches Passwort für Benutzer '{username}'")
                return None
            
            # Erfolgreiche Authentifizierung
            logger.info(f"Erfolgreiche Authentifizierung für Benutzer '{username}'")
            
            return {
                "username": username,
                "is_admin": user['is_admin']
            }
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei der Authentifizierung: {str(e)}", exc_info=True)
            return None
    
    def verify_token(self, token: str) -> Dict:
        """Verifiziert ein JWT-Token
        
        Args:
            token: JWT-Token
            
        Returns:
            Dict: Decodiertes Token
            
        Raises:
            HTTPException: Bei ungültigem Token
        """
        try:
            # Decodiere das Token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Überprüfe Token-Typ
            if payload.get("token_type") != "access":
                logger.warning("Versuch, ein Refresh-Token als Zugriffstoken zu verwenden")
                raise HTTPException(
                    status_code=401,
                    detail="Ungültiger Token-Typ"
                )
            
            # Überprüfe Ablaufdatum (wird bereits von jwt.decode geprüft)
            username = payload.get("sub")
            if username is None:
                logger.warning("Token enthält keinen Benutzernamen")
                raise HTTPException(
                    status_code=401,
                    detail="Ungültiges Token"
                )
            
            logger.info(f"Token erfolgreich verifiziert für Benutzer: {username}")
            return payload
        except ExpiredSignatureError:
            logger.warning("Token ist abgelaufen")
            raise HTTPException(
                status_code=401,
                detail="Token ist abgelaufen"
            )
        except PyJWTError as e:
            logger.error(f"Token-Verifikation fehlgeschlagen: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Token-Verifikation fehlgeschlagen"
            )
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei der Token-Verifikation: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Interner Authentifizierungsfehler"
            )
    
    def get_current_user(self, token: str = Depends(oauth2_scheme)) -> Dict:
        """Holt den aktuellen Benutzer aus dem Token
        
        Args:
            token: JWT-Token
            
        Returns:
            Dict: Benutzerdaten
            
        Raises:
            HTTPException: Bei ungültigem Token
        """
        try:
            payload = self.verify_token(token)
            username = payload.get("sub")
            
            if username is None:
                raise HTTPException(
                    status_code=401,
                    detail="Ungültiges Token"
                )
            
            # Hole Benutzerinformationen
            user = self.user_manager.get_user(username)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Benutzer nicht gefunden"
                )
            
            return {
                "username": username,
                "is_admin": user['is_admin']
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei der Benutzerabfrage: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Interner Authentifizierungsfehler"
            )
    
    def require_admin(self, request: Request) -> Dict:
        """Stellt sicher, dass der aktuelle Benutzer Admin-Rechte hat
        
        Args:
            request: FastAPI Request-Objekt
            
        Returns:
            Dict: Benutzerdaten
            
        Raises:
            HTTPException: Wenn der Benutzer kein Admin ist
        """
        try:
            user = self.get_current_user(request)
            
            if not user.get("is_admin", False):
                logger.warning(f"Zugriffsversuch auf Admin-Endpunkt durch Nicht-Admin: {user.get('username')}")
                raise HTTPException(
                    status_code=403,
                    detail="Admin-Rechte erforderlich"
                )
            
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei der Admin-Prüfung: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Interner Authentifizierungsfehler"
            )