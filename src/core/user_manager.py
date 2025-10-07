# src/core/user_manager.py
"""
user_manager.py - Benutzerverwaltung für Mindestentinel

Diese Datei implementiert die Benutzerverwaltung des Systems.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("mindestentinel.user_manager")

class UserManager:
    """Verwaltet die Benutzer des Systems"""
    
    def __init__(self, knowledge_base=None):
        """Initialisiert den UserManager
        
        Args:
            knowledge_base: Referenz zur Wissensdatenbank (optional)
        """
        self.kb = knowledge_base
        self.db_path = "data/users/users.db"
        self._init_db()
        logger.info("UserManager initialisiert.")
    
    def _init_db(self):
        """Initialisiert die Benutzerdatenbank"""
        try:
            # Erstelle Verzeichnis, falls nicht vorhanden
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Verbinde mit der Datenbank
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Erstelle Tabelle für Benutzer
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Füge Standard-Admin-Benutzer hinzu, falls nicht vorhanden
                cursor.execute("SELECT * FROM users WHERE username = 'admin'")
                if not cursor.fetchone():
                    # In einem echten System würden Sie das Passwort hashen
                    cursor.execute("""
                    INSERT INTO users (username, password, is_admin)
                    VALUES ('admin', 'SicheresNeuesPasswort123!', 1)
                    """)
                    conn.commit()
                    logger.info("Standard-Admin-Benutzer 'admin' erstellt.")
                else:
                    logger.info("Standard-Admin-Benutzer 'admin' existiert bereits")
                
                conn.commit()
                logger.info("Benutzerdatenbankstruktur initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Benutzerdatenbank: {str(e)}", exc_info=True)
            raise
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Holt einen Benutzer anhand des Benutzernamens
        
        Args:
            username: Benutzername
            
        Returns:
            Dict[str, Any]: Benutzerdaten oder None, wenn nicht gefunden
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT id, username, password, is_admin, created_at
                FROM users
                WHERE username = ?
                """, (username,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "username": row[1],
                        "password": row[2],
                        "is_admin": bool(row[3]),
                        "created_at": row[4]
                    }
                return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Benutzers: {str(e)}", exc_info=True)
            return None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """Listet alle Benutzer auf
        
        Returns:
            List[Dict[str, Any]]: Liste aller Benutzer
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT id, username, is_admin, created_at
                FROM users
                ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                return [{
                    "id": row[0],
                    "username": row[1],
                    "is_admin": bool(row[2]),
                    "created_at": row[3]
                } for row in rows]
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Benutzer: {str(e)}", exc_info=True)
            return []
    
    def update_password(self, username: str, new_password: str) -> bool:
        """Aktualisiert das Passwort eines Benutzers
        
        Args:
            username: Benutzername
            new_password: Neues Passwort
            
        Returns:
            bool: True bei Erfolg, sonst False
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE users
                SET password = ?
                WHERE username = ?
                """, (new_password, username))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Passwort für Benutzer '{username}' aktualisiert.")
                    return True
                return False
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Passworts: {str(e)}", exc_info=True)
            return False