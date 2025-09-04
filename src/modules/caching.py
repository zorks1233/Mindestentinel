# src/modules/caching.py
"""
Central caching layer (in-memory LRU + disk-backed optional).
- LRUCache class
- DiskCache class (simple file mapping)
"""

from __future__ import annotations
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

class LRUCache:
    def __init__(self, max_items: int = 1024):
        self.max_items = int(max_items)
        self._lock = threading.RLock()
        self._dict = OrderedDict()

    def get(self, key: str, default=None):
        with self._lock:
            if key not in self._dict:
                return default
            val = self._dict.pop(key)
            self._dict[key] = val
            return val

    def put(self, key: str, value: Any):
        with self._lock:
            if key in self._dict:
                self._dict.pop(key)
            self._dict[key] = value
            while len(self._dict) > self.max_items:
                self._dict.popitem(last=False)

    def evict(self, key: str):
        with self._lock:
            if key in self._dict:
                del self._dict[key]

    def clear(self):
        with self._lock:
            self._dict.clear()

class DiskCache:
    def __init__(self, base_dir: str = "data/cache"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        name = "".join(c for c in key if c.isalnum() or c in ("-", "_"))
        return self.base / f"{name}.cache"

    def get(self, key: str) -> Optional[bytes]:
        p = self._path(key)
        if not p.exists():
            return None
        return p.read_bytes()

    def put(self, key: str, data: bytes):
        p = self._path(key)
        p.write_bytes(data)

    def delete(self, key: str):
        p = self._path(key)
        if p.exists():
            p.unlink()
