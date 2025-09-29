# src/core/knowledge_base.py
"""
knowledge_base.py - Wissensdatenbank für Mindestentinel

Diese Datei implementiert die Wissensdatenbank für das System.
Es ermöglicht das Speichern, Abrufen und Verwalten von Wissen.
"""

import logging
import os
import sqlite3
import json
import base64
import time
from typing import Dict, Any, Optional, List, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

logger = logging.getLogger("mindestentinel.knowledge_base")

class KnowledgeBase:
    """
    Verwaltet die Wissensdatenbank für das System.
    
    Lädt, speichert und verwaltet Wissen und Metadaten.
    """
    
    def __init__(self, db_path: str = "data/knowledge/knowledge.db", encryption_key: Optional[bytes] = None):
        """
        Initialisiert die Wissensdatenbank.
        
        Args:
            db_path: Pfad zur Datenbankdatei
            encryption_key: Optionaler Verschlüsselungsschlüssel
        """
        # Erstelle das Datenbank-Verzeichnis, falls nicht vorhanden
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.encryption_key = encryption_key
        
        # Initialisiere das Verschlüsselungssystem
        self._initialize_encryption()
        
        # Initialisiere die Datenbankstruktur
        self._initialize_database()
        
        logger.info(f"Wissensdatenbank initialisiert: {self.db_path}")
    
    def _initialize_encryption(self):
        """Initialisiert das Verschlüsselungssystem."""
        # Generiere einen Schlüssel, falls keiner vorhanden ist
        if not self.encryption_key:
            try:
                # Versuche, den Schlüssel aus einer Datei zu laden
                key_path = os.path.join(os.path.dirname(self.db_path), "encryption.key")
                if os.path.exists(key_path):
                    with open(key_path, 'rb') as f:
                        self.encryption_key = f.read()
                else:
                    # Erstelle einen neuen Schlüssel
                    self.encryption_key = Fernet.generate_key()
                    with open(key_path, 'wb') as f:
                        f.write(self.encryption_key)
                    logger.info("Neuer Verschlüsselungsschlüssel generiert und gespeichert.")
            except Exception as e:
                logger.warning(f"Fehler bei der Schlüsselinitialisierung: {str(e)}. Verwende unverschlüsselten Modus.")
                self.encryption_key = None
        
        # Erstelle den Fernet-Handler
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
        logger.debug("Verschlüsselungssystem initialisiert.")
    
    def _initialize_database(self):
        """Initialisiert die Datenbankstruktur."""
        try:
            # Erstelle die Wissens-Tabelle, falls nicht vorhanden
            self.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    data TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            logger.info("Datenbankstruktur initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Datenbankstruktur: {str(e)}", exc_info=True)
    
    def execute(self, query: str, params: Tuple = ()) -> None:
        """
        Führt eine SQL-Abfrage aus (für INSERT, UPDATE, DELETE).
        
        Args:
            query: Die SQL-Abfrage
            params: Parameter für die Abfrage
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankausführung: {str(e)}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def select(self, query: str, params: Tuple = (), decrypt_column: Optional[int] = None) -> List[Tuple]:
        """
        Führt eine SELECT-Abfrage aus und gibt die Ergebnisse zurück.
        
        Args:
            query: Die SQL-Abfrage
            params: Parameter für die Abfrage
            decrypt_column: Index der Spalte, die entschlüsselt werden soll (optional)
            
        Returns:
            List[Tuple]: Die Ergebnisse der Abfrage
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Entschlüssele die angegebene Spalte, falls erforderlich
            if decrypt_column is not None and self.fernet:
                decrypted_results = []
                for row in results:
                    new_row = list(row)
                    try:
                        # Entschlüssele die angegebene Spalte
                        encrypted_data = row[decrypt_column]
                        if isinstance(encrypted_data, str):
                            decrypted_data = self.fernet.decrypt(encrypted_data.encode()).decode()
                            new_row[decrypt_column] = decrypted_data
                        decrypted_results.append(tuple(new_row))
                    except Exception as e:
                        logger.error(f"Fehler bei der Entschlüsselung: {str(e)}", exc_info=True)
                        decrypted_results.append(row)
                return decrypted_results
            
            return results
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankabfrage: {str(e)}", exc_info=True)
            return []
        finally:
            if conn:
                conn.close()
    
    def store(self, category: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Speichert Wissen in der Datenbank.
        
        Args:
            category: Die Kategorie des Wissens
            data: Die zu speichernden Daten
            metadata: Optionale Metadaten
            
        Returns:
            int: Die ID des gespeicherten Eintrags
        """
        try:
            # Verschlüssele die Daten, falls erforderlich
            encrypted_data = json.dumps(data)
            if self.fernet:
                encrypted_data = self.fernet.encrypt(encrypted_data.encode()).decode()
            
            # Vorbereiten der Metadaten
            metadata = metadata or {}
            metadata["category"] = category
            metadata["created_at"] = time.time()
            metadata["updated_at"] = time.time()
            
            # Speichern in der Datenbank
            self.execute(
                "INSERT INTO knowledge (category, data, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (category, encrypted_data, json.dumps(metadata), time.time(), time.time())
            )
            
            # Hole die ID des neuen Eintrags
            result = self.select("SELECT last_insert_rowid()")
            if result and len(result) > 0:
                return result[0][0]
            return -1
        except Exception as e:
            logger.error(f"Fehler beim Speichern von Wissen: {str(e)}", exc_info=True)
            return -1
    
    def get(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """
        Holt einen Wissenseintrag aus der Datenbank.
        
        Args:
            entry_id: Die ID des Eintrags
            
        Returns:
            Optional[Dict[str, Any]]: Der Wissenseintrag, falls gefunden, sonst None
        """
        try:
            result = self.select(
                "SELECT category, data, metadata FROM knowledge WHERE id = ?",
                (entry_id,),
                decrypt_column=1
            )
            
            if result:
                category, data, metadata = result[0]
                return {
                    "id": entry_id,
                    "category": category,
                    "data": json.loads(data),
                    "metadata": json.loads(metadata)
                }
            else:
                logger.warning(f"Wissenseintrag mit ID {entry_id} nicht gefunden.")
                return None
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Wissen: {str(e)}", exc_info=True)
            return None
    
    def query(self, category: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fragt Wissen nach Kategorie und Filtern ab.
        
        Args:
            category: Die Kategorie des Wissens
            filters: Optionale Filter
            
        Returns:
            List[Dict[str, Any]]: Die gefundenen Wissenseinträge
        """
        try:
            # Erstelle die WHERE-Klausel
            where_clauses = ["category = ?"]
            params = [category]
            
            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"json_extract(metadata, '$.{key}') = ?")
                    params.append(str(value))
            
            where_clause = " AND ".join(where_clauses)
            query = f"SELECT id, category, data, metadata FROM knowledge WHERE {where_clause}"
            
            results = self.select(query, tuple(params), decrypt_column=2)
            
            # Formatieren der Ergebnisse
            formatted_results = []
            for row in results:
                entry_id, category, data, metadata = row
                formatted_results.append({
                    "id": entry_id,
                    "category": category,
                    "data": json.loads(data),
                    "metadata": json.loads(metadata)
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Fehler bei der Wissensabfrage: {str(e)}", exc_info=True)
            return []
    
    def update(self, entry_id: int, data: Optional[Dict[str, Any]] = None, 
               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Aktualisiert einen Wissenseintrag.
        
        Args:
            entry_id: Die ID des Eintrags
            data: Optionale neue Daten
            metadata: Optionale neue Metadaten
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            # Hole den aktuellen Eintrag
            current = self.get(entry_id)
            if not current:
                return False
            
            # Vorbereiten der neuen Daten
            new_data = data if data is not None else current["data"]
            new_metadata = metadata if metadata is not None else current["metadata"]
            new_metadata["updated_at"] = time.time()
            
            # Verschlüssele die neuen Daten, falls erforderlich
            encrypted_data = json.dumps(new_data)
            if self.fernet:
                encrypted_data = self.fernet.encrypt(encrypted_data.encode()).decode()
            
            # Aktualisiere den Eintrag
            self.execute(
                "UPDATE knowledge SET data = ?, metadata = ?, updated_at = ? WHERE id = ?",
                (encrypted_data, json.dumps(new_metadata), time.time(), entry_id)
            )
            
            return True
        except Exception as e:
            logger.error(f"Fehler bei der Aktualisierung von Wissen: {str(e)}", exc_info=True)
            return False
    
    def delete(self, entry_id: int) -> bool:
        """
        Löscht einen Wissenseintrag.
        
        Args:
            entry_id: Die ID des Eintrags
            
        Returns:
            bool: True, wenn erfolgreich, sonst False
        """
        try:
            self.execute(
                "DELETE FROM knowledge WHERE id = ?",
                (entry_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen von Wissen: {str(e)}", exc_info=True)
            return False
    
    def list_categories(self) -> List[str]:
        """
        Listet alle Kategorien auf.
        
        Returns:
            List[str]: Die Kategorien
        """
        try:
            results = self.select("SELECT DISTINCT category FROM knowledge")
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Kategorien: {str(e)}", exc_info=True)
            return []