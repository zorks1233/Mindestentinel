# knowledge_base 
# src/core/knowledge_base.py
"""
KnowledgeBase - SQLite-basierte persistente Ablage für Texte/Artefakte.
- Tabellen: facts (key, value, ts)
- Methoden: store, query (simple LIKE), search (returns list), count_all, persist
"""

from __future__ import annotations
import sqlite3
import threading
import time
import os
from typing import List, Optional

DB_PATH_DEFAULT = os.path.join(os.getcwd(), "data", "knowledge", "kb.sqlite3")

class KnowledgeBase:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH_DEFAULT
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    content TEXT,
                    ts INTEGER
                )
            """)
            conn.commit()

    def store(self, source: str, content: str) -> int:
        """Speichert content mit Quellennennung. Gibt die erzeugte ID zurück."""
        ts = int(time.time())
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO facts (source, content, ts) VALUES (?, ?, ?)", (source, content, ts))
            conn.commit()
            return cur.lastrowid

    def query(self, query_text: str, limit: int = 50) -> List[str]:
        """Einfache Volltext-ähnliche Suche (LIKE)."""
        like = f"%{query_text}%"
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT content FROM facts WHERE content LIKE ? ORDER BY ts DESC LIMIT ?", (like, limit))
            rows = cur.fetchall()
            return [r[0] for r in rows]

    def search(self, source: str, limit: int = 100) -> List[str]:
        """Gibt Inhalte einer bestimmten Quelle zurück (z. B. 'self_learning')."""
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT content FROM facts WHERE source = ? ORDER BY ts DESC LIMIT ?", (source, limit))
            rows = cur.fetchall()
            return [r[0] for r in rows]

    def count_all(self) -> int:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) FROM facts")
            r = cur.fetchone()
            return int(r[0]) if r else 0

    def persist(self) -> None:
        """Operation für explizite Persistenz/Flush (hier kein-op, DB ist persistent)."""
        # kept for compatibility with ai_engine background loop
        return
