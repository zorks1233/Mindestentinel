# src/modules/utils/prefetching.py
"""
Simple predictive prefetching subsystem:
- register_candidate(key, loader_callable)
- start background thread to prefetch when idle
- LRU-ish in-memory cache of bytes up to a size limit
"""

from __future__ import annotations
import threading
import time
from collections import OrderedDict
from typing import Callable, Dict, Optional

class Prefetcher:
    def __init__(self, max_cache_bytes: int = 100 * 1024 * 1024, idle_check_interval: float = 5.0):
        self.max_cache_bytes = int(max_cache_bytes)
        self.idle_check_interval = float(idle_check_interval)
        self._candidates: Dict[str, Callable[[], bytes]] = {}
        self._cache: OrderedDict[str, bytes] = OrderedDict()
        self._cache_bytes = 0
        self._lock = threading.RLock()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._running = False

    def register_candidate(self, key: str, loader: Callable[[], bytes]) -> None:
        with self._lock:
            self._candidates[key] = loader

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            if key in self._cache:
                val = self._cache.pop(key)
                # reinsert to maintain LRU
                self._cache[key] = val
                return val
            return None

    def _evict_if_needed(self):
        with self._lock:
            while self._cache_bytes > self.max_cache_bytes and self._cache:
                k, v = self._cache.popitem(last=False)
                self._cache_bytes -= len(v)

    def _loop(self):
        while self._running:
            # simple heuristic: try to prefetch first candidate not in cache
            with self._lock:
                candidates = list(self._candidates.items())
            for key, loader in candidates:
                with self._lock:
                    if key in self._cache:
                        continue
                try:
                    data = loader()
                    if not data:
                        continue
                    with self._lock:
                        self._cache[key] = data
                        self._cache_bytes += len(data)
                        # ensure LRU order
                        self._evict_if_needed()
                except Exception:
                    # ignore loader exceptions; don't kill loop
                    pass
                # short sleep between candidate fetches to avoid hogging
                time.sleep(0.1)
            time.sleep(self.idle_check_interval)
