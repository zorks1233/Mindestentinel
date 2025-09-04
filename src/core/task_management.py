# task_management 
# src/core/task_management.py
"""
TaskManagement - persistente Task-Queue basierend auf SQLite.
- DB: data/tasks.db (table tasks)
- Methoden: add_task, get_tasks, complete_task, pop_next_task, count_pending
- Thread-safe
"""

from __future__ import annotations
import sqlite3
import threading
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import os

DB_PATH = Path("data") / "tasks.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

class TaskManagement:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    created_ts INTEGER,
                    updated_ts INTEGER
                )
            """)
            conn.commit()

    def add_task(self, description: str, priority: int = 0) -> int:
        now = int(time.time())
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO tasks (description, status, priority, created_ts, updated_ts) VALUES (?, ?, ?, ?, ?)",
                        (description, "pending", int(priority), now, now))
            conn.commit()
            return cur.lastrowid

    def get_tasks(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            if status:
                cur.execute("SELECT id, description, status, priority, created_ts, updated_ts FROM tasks WHERE status=? ORDER BY priority DESC, created_ts ASC LIMIT ?", (status, limit))
            else:
                cur.execute("SELECT id, description, status, priority, created_ts, updated_ts FROM tasks ORDER BY priority DESC, created_ts ASC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [{"id": r[0], "description": r[1], "status": r[2], "priority": r[3], "created_ts": r[4], "updated_ts": r[5]} for r in rows]

    def complete_task(self, task_id: int) -> bool:
        now = int(time.time())
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE tasks SET status=?, updated_ts=? WHERE id=?", ("done", now, task_id))
            conn.commit()
            return cur.rowcount > 0

    def pop_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Atomically fetch next pending task (highest priority, oldest first) and mark as 'in_progress'.
        Returns the task dict or None.
        """
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # Use a transaction to avoid races
            cur.execute("BEGIN IMMEDIATE")
            cur.execute("SELECT id FROM tasks WHERE status=? ORDER BY priority DESC, created_ts ASC LIMIT 1", ("pending",))
            row = cur.fetchone()
            if not row:
                conn.commit()
                return None
            task_id = row[0]
            now = int(time.time())
            cur.execute("UPDATE tasks SET status=?, updated_ts=? WHERE id=?", ("in_progress", now, task_id))
            cur.execute("SELECT id, description, status, priority, created_ts, updated_ts FROM tasks WHERE id=?", (task_id,))
            task_row = cur.fetchone()
            conn.commit()
            return {"id": task_row[0], "description": task_row[1], "status": task_row[2], "priority": task_row[3], "created_ts": task_row[4], "updated_ts": task_row[5]}

    def count_pending(self) -> int:
        with self._lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) FROM tasks WHERE status=?", ("pending",))
            r = cur.fetchone()
            return int(r[0]) if r else 0
