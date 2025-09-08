# src/core/knowledge_base.py
"""
KnowledgeBase - Verwaltet die Wissensdatenbank des Systems
"""

import logging
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """
    Verwaltet die Wissensdatenbank des Systems.
    Speichert Fakten, Interaktionen und Metadaten in einer SQLite-Datenbank.
    """
    
    def __init__(self, db_path: str = "data/knowledge/knowledge.db"):
        """
        Initialisiert die Wissensdatenbank.
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialisiere die Datenbank
        self._init_db()
        logger.info(f"Wissensdatenbank initialisiert: {self.db_path}")
    
    def _init_db(self):
        """Initialisiert die Datenbankstruktur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabelle für Fakten
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Tabelle für Benutzerinteraktionen
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Tabelle für Metadaten
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """)
                
                # Initialisiere Versionsnummer
                cursor.execute("""
                INSERT OR IGNORE INTO metadata (key, value) VALUES ('version', '1.0')
                """)
                
                conn.commit()
                logger.debug("Datenbankstruktur initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Datenbank: {str(e)}", exc_info=True)
            raise
    
    def store(self, source: str, content: Any, ts: Optional[str] = None):
        """
        Speichert einen Eintrag in der Wissensdatenbank.
        
        Args:
            source: Quelle des Eintrags
            content: Inhalt (wird als JSON serialisiert, wenn es ein Dict ist)
            ts: Optionale Zeitstempel
        """
        # Serialisiere Dictionaries als JSON
        if isinstance(content, dict) or isinstance(content, list):
            content = json.dumps(content)
        elif not isinstance(content, str):
            content = str(content)
        
        # Verwende aktuellen Zeitstempel, falls keiner angegeben
        if ts is None:
            ts = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO facts (source, content, ts) VALUES (?, ?, ?)",
                    (source, content, ts)
                )
                conn.commit()
                logger.debug(f"Eintrag gespeichert: {source} ({len(content)} Zeichen)")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Eintrags: {str(e)}", exc_info=True)
            raise
    
    def query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Führt eine SQL-Abfrage aus und gibt die Ergebnisse als Liste von Dictionaries zurück.
        
        Args:
            sql: Die SQL-Abfrage
            params: Optionale Parameter für die Abfrage
            
        Returns:
            Liste von Dictionaries mit den Ergebnissen
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage: {str(e)}\nSQL: {sql}", exc_info=True)
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Wissensdatenbank zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Gesamtanzahl der Einträge
                cursor.execute("SELECT COUNT(*) as count FROM facts")
                total_entries = cursor.fetchone()[0]
                
                # Anzahl der Einträge pro Quelle
                cursor.execute("SELECT source, COUNT(*) as count FROM facts GROUP BY source")
                source_counts = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Letzte Aktualisierung
                cursor.execute("SELECT MAX(ts) as last_update FROM facts")
                last_update = cursor.fetchone()[0]
                
                return {
                    "total_entries": total_entries,
                    "entries_by_source": source_counts,
                    "last_update": last_update
                }
        except Exception as e:
            logger.error(f"Fehler bei der Statistikabfrage: {str(e)}", exc_info=True)
            return {
                "total_entries": 0,
                "entries_by_source": {},
                "last_update": None
            }
    
    def store_interaction(self, user_id: str, query: str, response: str):
        """
        Speichert eine Benutzerinteraktion.
        
        Args:
            user_id: ID des Benutzers
            query: Benutzeranfrage
            response: Systemantwort
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO user_interactions (user_id, query, response) VALUES (?, ?, ?)",
                    (user_id, query, response)
                )
                conn.commit()
                logger.debug(f"Benutzerinteraktion gespeichert: {user_id}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Benutzerinteraktion: {str(e)}", exc_info=True)
    
    def get_recent_interactions(self, user_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Gibt die neuesten Benutzerinteraktionen zurück.
        
        Args:
            user_id: Optionale Benutzer-ID zur Filterung
            limit: Maximale Anzahl der zurückzugebenden Interaktionen
            
        Returns:
            Liste von Interaktionen
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute(
                        "SELECT * FROM user_interactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                        (user_id, limit)
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM user_interactions ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Fehler bei der Abfrage von Benutzerinteraktionen: {str(e)}", exc_info=True)
            return []
    
    def persist(self):
        """Führt eine persistente Speicherung durch (hier noop, da SQLite bereits persistiert)"""
        logger.debug("Wissensdatenbank persistiert (noop)")