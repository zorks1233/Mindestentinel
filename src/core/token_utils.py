# src/core/token_utils.py
"""
token_utils.py - Zentraler JWT-Wrapper für Mindestentinel

Diese Datei implementiert einen sicheren JWT-Wrapper, der:
- alg='none' verbietet
- Token-Ablaufzeiten erzwingt
- Zentrale Validierung und Erstellung von Tokens bietet
"""

from __future__ import annotations
import os
import time
import jwt
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("mindestentinel.token_utils")

class JWTError(Exception):
    """Basis-Exception für JWT-bezogene Fehler"""
    pass

def create_token(payload: Dict[str, Any], 
                 secret: str,
                 algorithm: str = "HS256",
                 exp_seconds: int = 3600) -> str:
    """
    Erstellt ein JWT-Token mit Ablaufzeit.
    
    Args:
        payload: Die Nutzdaten für das Token
        secret: Der geheime Schlüssel für die Signatur
        algorithm: Der verwendete Algorithmus (Standard: HS256)
        exp_seconds: Ablaufzeit in Sekunden (Standard: 3600)
        
    Returns:
        str: Das signierte JWT-Token
    """
    # Prüfe, ob alg='none' versucht wird
    if algorithm.lower() == "none":
        logger.error("Versuch, JWT mit alg='none' zu erstellen - BLOCKIERT")
        raise JWTError("JWT alg 'none' ist durch Sicherheitsrichtlinien verboten")
    
    # Erstelle das Token mit Ablaufzeit
    data = payload.copy()
    data["iat"] = int(time.time())
    data["exp"] = int(time.time()) + exp_seconds
    
    return jwt.encode(data, secret, algorithm=algorithm)

def decode_token(token: str, secret: str, algorithm: str = "HS256") -> Dict[str, Any]:
    """
    Validiert und decodiert ein JWT-Token.
    
    Args:
        token: Das zu decodierende Token
        secret: Der geheime Schlüssel für die Verifikation
        algorithm: Der verwendete Algorithmus (Standard: HS256)
        
    Returns:
        Dict[str, Any]: Die decodierten Nutzdaten
        
    Raises:
        JWTError: Wenn das Token ungültig ist
    """
    try:
        # Prüfe, ob das Token leer ist
        if not token:
            logger.warning("Versuch, leeres Token zu decodieren")
            raise JWTError("Token ist leer")
        
        # Entferne 'Bearer ' Prefix, falls vorhanden
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Decodiere das Token
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        
        # Prüfe Ablaufzeit
        current_time = int(time.time())
        if "exp" in payload and payload["exp"] < current_time:
            logger.warning(f"Token ist abgelaufen (exp: {payload['exp']}, now: {current_time})")
            raise JWTError("Token ist abgelaufen")
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token ist abgelaufen")
        raise JWTError("Token ist abgelaufen")
    except jwt.InvalidTokenError as e:
        logger.error(f"Ungültiges Token: {str(e)}")
        raise JWTError(f"Ungültiges Token: {str(e)}")
    except Exception as e:
        logger.error(f"Unbekannter Fehler bei der Token-Verifikation: {str(e)}")
        raise JWTError(f"Token-Verifikation fehlgeschlagen: {str(e)}")

def validate_token(token: str, secret: str, algorithm: str = "HS256") -> bool:
    """
    Überprüft, ob ein Token gültig ist.
    
    Args:
        token: Das zu überprüfende Token
        secret: Der geheime Schlüssel für die Verifikation
        algorithm: Der verwendete Algorithmus (Standard: HS256)
        
    Returns:
        bool: True, wenn das Token gültig ist, sonst False
    """
    try:
        decode_token(token, secret, algorithm)
        return True
    except JWTError:
        return False