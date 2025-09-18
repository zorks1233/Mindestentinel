# src/core/knowledge_base.py
"""
knowledge_base.py - Verschlüsselte Wissensdatenbank für Mindestentinel

Diese Datei implementiert eine verschlüsselte SQLite-Datenbank für das Speichern von Wissen.
Alle sensiblen Daten werden vor dem Speichern verschlüsselt und nach dem Abrufen entschlüsselt.
"""

import logging
import sqlite3
import os
import json
from typing import Dict, Any, List, Optional, Tuple
import datetime
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("mindestentinel.knowledge_base")

class KnowledgeBase:
    """
    Verschlüsselte Wissensdatenbank für Mindestentinel.
    
    Alle Daten werden vor dem Speichern verschlüsselt und nach dem Abrufen entschlüsselt.
    Verwendet Fernet (symmetrische Verschlüsselung) für die Datensicherheit.
    """
    
    def __init__(self, db_path: str = "data/knowledge/knowledge.db", key_path: str = "data/knowledge/encryption.key"):
        """
        Initialisiert die verschlüsselte Wissensdatenbank.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
            key_path: Pfad zum Verschlüsselungsschlüssel
        """
        self.db_path = db_path
        self.key_path = key_path
        
        # Erstelle Verzeichnisse, falls nicht vorhanden
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialisiere Verschlüsselung
        self._init_encryption()
        
        # Initialisiere Datenbank
        self._init_db()
        
        logger.info(f"Wissensdatenbank initialisiert: {db_path}")
    
    def _init_encryption(self):
        """Initialisiert die Verschlüsselung für die Datenbank."""
        # Falls Schlüssel nicht existiert, erstelle einen neuen
        if not os.path.exists(self.key_path):
            # Generiere einen sicheren Schlüssel
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
            with open(self.key_path, 'wb') as f:
                f.write(key)
            logger.info("Neuer Verschlüsselungsschlüssel generiert und gespeichert.")
        
        # Lade den Schlüssel
        with open(self.key_path, 'rb') as f:
            key = f.read()
        
        # Initialisiere den Verschlüsselungscipher
        self.cipher = Fernet(key)
        logger.debug("Verschlüsselungssystem initialisiert.")
    
    def _init_db(self):
        """Initialisiert die Datenbankstruktur."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Erstelle die Haupttabelle für Wissen
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                encrypted_data BLOB NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
            """)
            
            # Erstelle eine Tabelle für Systemstatistiken
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT NOT NULL,
                encrypted_value BLOB NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Erstelle eine Tabelle für Lernhistorie
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id TEXT NOT NULL,
                encrypted_data BLOB NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Erstelle Benutzertabelle, falls nicht vorhanden
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Datenbankstruktur initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankinitialisierung: {str(e)}", exc_info=True)
            raise
    
    def store(self, category: str, data: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> int:
        """
        Speichert Daten in der Wissensdatenbank.
        
        Args:
            category: Die Kategorie der Daten
            data: Die zu speichernden Daten
            meta: Optionale Metadaten
            
        Returns:
            int: Die ID des gespeicherten Eintrags
        """
        try:
            # Verschlüssele die Daten
            encrypted_data = self._encrypt_data(data)
            
            # Vorbereiten der Metadaten
            metadata_json = json.dumps(meta) if meta else None
            
            # Speichere in der Datenbank
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO knowledge (category, encrypted_data, metadata)
            VALUES (?, ?, ?)
            """, (category, encrypted_data, metadata_json))
            
            entry_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.debug(f"Gespeichert: Kategorie={category}, ID={entry_id}")
            return entry_id
        except Exception as e:
            logger.error(f"Fehler beim Speichern in der Wissensdatenbank: {str(e)}", exc_info=True)
            raise
    
    def query(self, sql: str, params: tuple = ()) -> int:
        """
        Führt eine Abfrage auf der Datenbank aus.
        
        Args:
            sql: Die SQL-Abfrage
            params: Optionale Parameter für die Abfrage
            
        Returns:
            int: Anzahl betroffener Zeilen
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            
            # Hole die Anzahl betroffener Zeilen
            affected_rows = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return affected_rows
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankabfrage: {str(e)}", exc_info=True)
            raise
    
    def select(self, sql: str, params: tuple = (), decrypt_column: Optional[int] = 2) -> List[Dict[str, Any]]:
        """
        Führt eine SELECT-Abfrage auf der Datenbank aus und entschlüsselt optionale Spalten.
        
        Args:
            sql: Die SQL-Abfrage
            params: Optionale Parameter für die Abfrage
            decrypt_column: Die Spalte, die entschlüsselt werden soll (None für keine Entschlüsselung)
            
        Returns:
            List[Dict[str, Any]]: Die Ergebnisse als Dictionary mit Spaltennamen
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            
            # Hole die Spaltennamen
            column_names = [description[0] for description in cursor.description]
            
            results = []
            for row in cursor.fetchall():
                result = {}
                
                # Verarbeite jede Spalte
                for i, value in enumerate(row):
                    column_name = column_names[i]
                    
                    # Soll die Spalte entschlüsselt werden?
                    if i == decrypt_column:
                        try:
                            # Entschlüssle die Daten
                            decrypted_data = self._decrypt_data(value)
                            result[column_name] = decrypted_data
                        except Exception as e:
                            logger.error(f"Fehler bei der Datenentschlüsselung für Spalte {column_name}: {str(e)}", exc_info=True)
                            result[column_name] = None
                    else:
                        # Verwende die Rohdaten
                        result[column_name] = value
                
                results.append(result)
            
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankabfrage: {str(e)}", exc_info=True)
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Wissensdatenbank zurück.
        
        Returns:
            Dict[str, Any]: Statistikinformationen
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Hole die Gesamtanzahl der Einträge
            cursor.execute("SELECT COUNT(*) FROM knowledge")
            total_entries = cursor.fetchone()[0]
            
            # Hole Einträge nach Kategorie
            cursor.execute("SELECT category, COUNT(*) FROM knowledge GROUP BY category")
            category_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Hole den neuesten Eintrag
            cursor.execute("SELECT timestamp FROM knowledge ORDER BY timestamp DESC LIMIT 1")
            latest_entry = cursor.fetchone()
            
            conn.close()
            
            return {
                "total_entries": total_entries,
                "category_counts": category_counts,
                "latest_entry": latest_entry[0] if latest_entry else None,
                "encrypted": True
            }
        except Exception as e:
            logger.error(f"Fehler bei der Statistikabfrage: {str(e)}", exc_info=True)
            return {
                "total_entries": 0,
                "category_counts": {},
                "latest_entry": None,
                "encrypted": True
            }
    
    def is_integrity_valid(self) -> bool:
        """
        Prüft die Integrität der Datenbank.
        
        Returns:
            bool: True, wenn die Integrität gewährleistet ist
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prüfe, ob die Tabellen existieren
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['knowledge', 'system_stats', 'learning_history', 'users']
            if not all(table in tables for table in required_tables):
                logger.error("Datenbankstruktur ist beschädigt - fehlende Tabellen")
                return False
            
            # Prüfe die Verschlüsselung
            cursor.execute("SELECT encrypted_data FROM knowledge LIMIT 1")
            if cursor.fetchone():
                # Versuche, einen Datensatz zu entschlüsseln
                try:
                    self._decrypt_data(cursor.fetchone()[0])
                except Exception as e:
                    logger.error(f"Verschlüsselungsintegrität fehlgeschlagen: {str(e)}")
                    return False
            
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Integritätsprüfung fehlgeschlagen: {str(e)}", exc_info=True)
            return False
    
    def _encrypt_data(self, data: Dict[str, Any]) -> bytes:
        """
        Verschlüsselt Daten.
        
        Args:
            data: Die zu verschlüsselnden Daten
            
        Returns:
            bytes: Die verschlüsselten Daten
        """
        try:
            # Serialisiere die Daten als JSON
            data_json = json.dumps(data).encode('utf-8')
            
            # Verschlüssele die Daten
            encrypted_data = self.cipher.encrypt(data_json)
            
            return encrypted_data
        except Exception as e:
            logger.error(f"Fehler bei der Datenverschlüsselung: {str(e)}", exc_info=True)
            raise
    
    def _decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Entschlüsselt Daten.
        
        Args:
            encrypted_data: Die zu entschlüsselnden Daten
            
        Returns:
            Dict[str, Any]: Die entschlüsselten Daten
        """
        try:
            # Sicherstellen, dass encrypted_data Bytes sind
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode('utf-8')
            
            # Entschlüssle die Daten
            decrypted_data = self.cipher.decrypt(encrypted_data)
            
            # Deserialisiere die JSON-Daten
            data = json.loads(decrypted_data.decode('utf-8'))
            
            return data
        except Exception as e:
            logger.error(f"Fehler bei der Datenentschlüsselung: {str(e)}", exc_info=True)
            raise