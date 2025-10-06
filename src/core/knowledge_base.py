# src/core/knowledge_base.py
"""
knowledge_base.py - Wissensdatenbank für Mindestentinel

Diese Datei implementiert die Wissensdatenbank für das System.
"""

import os
import sqlite3
import logging
from typing import List, Tuple, Optional, Dict, Any, Union

logger = logging.getLogger("mindestentinel.knowledge_base")

class KnowledgeBase:
    """Verwaltet die Wissensdatenbank"""
    
    def __init__(self, db_path: str = None):
        """Initialisiert die Wissensdatenbank
        
        Args:
            db_path: Pfad zur SQLite-Datenbank
        """
        # Bestimme den absoluten Pfad zur Datenbank
        if db_path is None:
            # WICHTIG: Verwende immer denselben Pfad, unabhängig davon, wo die Datei aufgerufen wird
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, "data", "knowledge", "knowledge.db")
        
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        logger.info(f"Wissensdatenbank initialisiert: {self.db_path}")
        
        # Initialisiere die Datenbankstruktur
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialisiert die Datenbankstruktur"""
        try:
            # Erstelle die Verbindung nur für die Initialisierung
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Erstelle die Wissens-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence FLOAT DEFAULT 1.0
                )
            """)
            
            # Erstelle die Benutzertabelle (wird von UserManager verwendet)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_admin BOOLEAN NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Erstelle die Modelle-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    path TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config TEXT,
                    categories TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Erstelle die Regeln-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Erstelle die Lernsitzungen-Tabelle
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT NOT NULL,
                    goals TEXT,
                    results TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Datenbankstruktur initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung der Datenbankstruktur: {str(e)}", exc_info=True)
            raise
    
    def execute(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Führt eine SQL-Abfrage aus, die Daten verändert
        
        Args:
            query: SQL-Abfrage
            params: Parameter für die Abfrage
            
        Returns:
            int: Anzahl der betroffenen Zeilen
        """
        try:
            # Erstelle eine neue Verbindung für jede Abfrage
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            rowcount = cursor.rowcount
            conn.close()
            return rowcount
        except Exception as e:
            logger.error(f"Fehler bei der Datenbankausführung: {str(e)}", exc_info=True)
            raise
    
    def query(self, query: str, params: Optional[Tuple] = None, filters: Optional[Dict] = None) -> List[Tuple]:
        """
        Führt eine SQL-Abfrage aus, die Daten abfragt
        
        Args:
            query: SQL-Abfrage
            params: Parameter für die Abfrage
            filters: Optionale Filter für die Ergebnisse
            
        Returns:
            List[Tuple]: Liste der Ergebnisse
        """
        try:
            # Erstelle eine neue Verbindung für jede Abfrage
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            conn.close()
            
            # Filtere die Ergebnisse, falls nötig
            if filters and isinstance(filters, dict):
                filtered_results = []
                for row in results:
                    include = True
                    for key, value in filters.items():
                        # Bestimme den Index des Feldes basierend auf der Abfrage
                        if key.isdigit():
                            idx = int(key)
                        else:
                            # Für dieses Beispiel nehmen wir an, dass der Index mit dem Schlüssel übereinstimmt
                            idx = int(key)
                        
                        if idx < len(row) and row[idx] != value:
                            include = False
                            break
                    
                    if include:
                        filtered_results.append(row)
                
                return filtered_results
            
            return results
        except Exception as e:
            logger.error(f"Fehler bei der Wissensabfrage: {str(e)}", exc_info=True)
            raise
    
    def add_knowledge(self, context: str, content: str, source: Optional[str] = None, confidence: float = 1.0):
        """
        Fügt neues Wissen zur Datenbank hinzu
        
        Args:
            context: Kontext des Wissens
            content: Inhalt des Wissens
            source: Quelle des Wissens
            confidence: Vertrauenswert des Wissens
        """
        try:
            self.execute(
                "INSERT INTO knowledge (context, content, source, confidence) VALUES (?, ?, ?, ?)",
                (context, content, source, confidence)
            )
            logger.info(f"Wissen hinzugefügt: {context}")
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen von Wissen: {str(e)}", exc_info=True)
    
    def get_knowledge(self, context: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Holt Wissen aus der Datenbank
        
        Args:
            context: Optionaler Kontext zum Filtern
            limit: Maximale Anzahl der Ergebnisse
            
        Returns:
            List[Dict]: Liste der Wissenseinträge
        """
        try:
            if context:
                results = self.query(
                    "SELECT * FROM knowledge WHERE context = ? ORDER BY timestamp DESC LIMIT ?",
                    (context, limit)
                )
            else:
                results = self.query(
                    "SELECT * FROM knowledge ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            
            # Konvertiere die Ergebnisse in ein Wörterbuch
            knowledge_list = []
            for row in results:
                knowledge_list.append({
                    'id': row[0],
                    'context': row[1],
                    'content': row[2],
                    'source': row[3],
                    'timestamp': row[4],
                    'confidence': row[5]
                })
            
            return knowledge_list
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Wissen: {str(e)}", exc_info=True)
            return []
    
    def close(self):
        """Schließt die Datenbankverbindung"""
        # Da wir keine persistente Verbindung haben, ist dies nicht nötig
        pass