# src/core/passwords.py
"""
passwords.py - Sicheres Passwort-Hashing für Mindestentinel

Diese Datei implementiert sicheres Passwort-Hashing mit bcrypt.
"""

import bcrypt
import logging
from typing import Union

logger = logging.getLogger("mindestentinel.passwords")

def hash_password(password: str) -> str:
    """
    Hashed ein Passwort mit bcrypt.
    
    Args:
        password: Das zu hashende Passwort
        
    Returns:
        str: Der gehashte Passwort-String
    """
    try:
        # Konvertiere das Passwort in Bytes
        password_bytes = password.encode('utf-8')
        
        # Generiere einen Salt und hash das Passwort
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Gib den gehashten String als UTF-8 zurück
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Fehler beim Hashen des Passworts: {str(e)}", exc_info=True)
        raise

def verify_password(password: str, hashed: str) -> bool:
    """
    Verifiziert ein Passwort gegen einen gespeicherten Hash.
    
    Args:
        password: Das zu prüfende Passwort
        hashed: Der gespeicherte Hash
        
    Returns:
        bool: True, wenn das Passwort korrekt ist, sonst False
    """
    try:
        # Konvertiere die Strings in Bytes
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        
        # Verifiziere das Passwort
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Fehler bei der Passwortverifikation: {str(e)}", exc_info=True)
        return False

def is_strong_password(password: str) -> Union[bool, str]:
    """
    Prüft, ob ein Passwort stark genug ist.
    
    Args:
        password: Das zu prüfende Passwort
        
    Returns:
        Union[bool, str]: True, wenn stark genug, sonst eine Fehlermeldung
    """
    if len(password) < 12:
        return "Passwort muss mindestens 12 Zeichen lang sein"
    
    if not any(c.isupper() for c in password):
        return "Passwort muss mindestens einen Großbuchstaben enthalten"
    
    if not any(c.islower() for c in password):
        return "Passwort muss mindestens einen Kleinbuchstaben enthalten"
    
    if not any(c.isdigit() for c in password):
        return "Passwort muss mindestens eine Ziffer enthalten"
    
    special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>/?"
    if not any(c in special_chars for c in password):
        return "Passwort muss mindestens ein Sonderzeichen enthalten"
    
    # Prüfe auf häufige Passwörter
    common_passwords = ["password", "123456", "qwerty", "admin", "welcome"]
    if any(pw in password.lower() for pw in common_passwords):
        return "Passwort enthält zu häufige Zeichenkombinationen"
    
    return True