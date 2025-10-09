# src/core/knowledge_base.py
"""
knowledge_base.py - Wissensdatenbank für Mindestentinel

Diese Datei implementiert die Wissensdatenbank des Systems.
"""

import logging
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


logger = logging.getLogger("mindestentinel.knowledge_base")

class KnowledgeBase:
    """Verwaltet die Wissensdatenbank des Systems"""

    def __init__(self, db_path: str = "data/knowledge/knowledge.db"):
        """Initialisiert die Wissensdatenbank

        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        self._init_db()
        logger.info(f"Wissensdatenbank initialisiert: {db_path}")

    def _init_db(self):
        """Initialisiert die Datenbankstruktur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Erstelle Tabelle für Wissen
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence FLOAT DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                # Erstelle Tabelle für Interaktionen
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    meta TEXT
                )
                """)

                conn.commit()
                logger.info("Datenbankstruktur initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Datenbank: {str(e)}", exc_info=True)
            raise

    def add_knowledge(self, context: str, content: str, source: str, confidence: float = 1.0):
        """Fügt neues Wissen zur Datenbank hinzu

        Args:
            context: Kontext des Wissens
            content: Inhalt des Wissens
            source: Quelle des Wissens
            confidence: Vertrauenswert des Wissens
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO knowledge (context, content, source, confidence)
                VALUES (?, ?, ?, ?)
                """, (context, content, source, confidence))
                conn.commit()
                logger.debug(f"Wissen hinzugefügt: {context} ({source})")
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen von Wissen: {str(e)}", exc_info=True)

    def get_knowledge(self, context: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Holt Wissen aus der Datenbank

        Args:
            context: Optionaler Kontext-Filter
            limit: Maximale Anzahl der Ergebnisse

        Returns:
            List[Dict[str, Any]]: Liste der Wissenseinträge
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if context:
                    cursor.execute("""
                    SELECT id, context, content, source, confidence, created_at
                    FROM knowledge
                    WHERE context = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """, (context, limit))
                else:
                    cursor.execute("""
                    SELECT id, context, content, source, confidence, created_at
                    FROM knowledge
                    ORDER BY created_at DESC
                    LIMIT ?
                    """, (limit,))

                rows = cursor.fetchall()
                return [{
                    "id": row[0],
                    "context": row[1],
                    "content": row[2],
                    "source": row[3],
                    "confidence": row[4],
                    "created_at": row[5]
                } for row in rows]
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Wissen: {str(e)}", exc_info=True)
            return []

    def get_recent_interactions(self, limit: int = 32) -> List[Dict[str, Any]]:
        """Holt die neuesten Interaktionen

        Args:
            limit: Maximale Anzahl der Interaktionen

        Returns:
            List[Dict[str, Any]]: Liste der Interaktionen
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT id, timestamp, role, content, meta
                FROM interactions
                ORDER BY id DESC
                LIMIT ?
                """, (limit,))

                rows = cursor.fetchall()
                results = []
                for r in rows:
                    meta = None
                    try:
                        if r[4]:
                            meta = json.loads(r[4])
                    except:
                        pass

                    results.append({
                        "id": r[0],
                        "timestamp": r[1],
                        "role": r[2],
                        "content": r[3],
                        "meta": meta
                    })
                return results
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der neuesten Interaktionen: {str(e)}", exc_info=True)
            return []

    def add_interaction(self, role: str, content: str, meta: Optional[Dict] = None):
        """Fügt eine neue Interaktion zur Datenbank hinzu

        Args:
            role: Rolle der Interaktion (user, assistant, system)
            content: Inhalt der Interaktion
            meta: Optionale Metadaten
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            meta_str = json.dumps(meta) if meta else None

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO interactions (timestamp, role, content, meta)
                VALUES (?, ?, ?, ?)
                """, (timestamp, role, content, meta_str))
                conn.commit()
                logger.debug(f"Interaktion hinzugefügt: {role}")
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen einer Interaktion: {str(e)}", exc_info=True)
