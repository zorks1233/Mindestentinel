# self_learning 
# src/core/self_learning.py
"""
SelfLearning - Produktionsfähiges Modul für autonome Lernschleifen.
- Verwaltet Ingested-Learning-Items, Batch-Verarbeitung und GPU-Request-Logging.
- Speichert Ergebnisse in KnowledgeBase (SQLite).
"""

from __future__ import annotations
import threading
import time
import uuid
import logging
from typing import List, Optional

_LOGGER = logging.getLogger("mindestentinel.self_learning")
_LOGGER.addHandler(logging.NullHandler())

class SelfLearning:
    def __init__(self, knowledge_base, max_history: int = 10000):
        """
        knowledge_base: Instanz von src.core.knowledge_base.KnowledgeBase
        """
        self.kb = knowledge_base
        self._lock = threading.RLock()
        self._incoming: List[str] = []
        self.max_history = max_history
        self.plugins = []
        self._requests = {}  # in-memory cache of gpu requests until persisted

    def register_plugin(self, plugin_obj) -> None:
        """Registriert ein Plugin, das Lernitems vorverarbeiten kann (optional)."""
        if not hasattr(plugin_obj, "name"):
            raise ValueError("Plugin muss 'name' Attribut besitzen")
        self.plugins.append(plugin_obj)
        _LOGGER.info("Plugin für SelfLearning registriert: %s", plugin_obj.name)

    def learn_from_input(self, input_text: str) -> str:
        """Fügt Text zur Lern-Queue hinzu und persistet minimal (schnell)."""
        if not input_text:
            raise ValueError("input_text darf nicht leer sein")
        with self._lock:
            # einfache de-dupe / cap
            if len(self._incoming) >= self.max_history:
                self._incoming.pop(0)
            self._incoming.append(input_text)
            # persist sofort in KB (quelle=self_learning_queue)
            self.kb.store("self_learning_queue", input_text)
        _LOGGER.debug("Neues Lern-Input aufgenommen (len_queue=%d)", len(self._incoming))
        return "queued"

    def batch_learn(self, max_items: int = 32) -> int:
        """
        Verarbeitet bis zu max_items aus der Queue:
        - optional Plugin-Vorverarbeitung
        - speichert verarbeitete Items in knowledge base als 'self_learning'
        - gibt die Anzahl verarbeiteter Items zurück
        """
        to_process = []
        with self._lock:
            while self._incoming and len(to_process) < max_items:
                to_process.append(self._incoming.pop(0))

        processed = 0
        for item in to_process:
            try:
                processed_item = item
                # plugin pipeline (synchron)
                for p in self.plugins:
                    if hasattr(p, "process"):
                        processed_item = p.process(processed_item)
                # store processed item
                self.kb.store("self_learning", processed_item)
                processed += 1
            except Exception as e:
                _LOGGER.exception("Fehler beim Verarbeiten eines Lern-Items: %s", e)

        _LOGGER.info("Batch-Learn abgeschlossen: %d Items verarbeitet", processed)
        return processed

    def perform_optimization(self) -> dict:
        """
        Einfacher Optimizer: Analysiert KB-Wachstum und gibt Empfehlungen.
        (Produktionsfähig: gibt Metriken, keine Blackbox-Optimierung.)
        """
        stats = {
            "total_items": self.kb.count_all(),
            "last_run": int(time.time()),
        }
        _LOGGER.info("Optimization run: %s", stats)
        return stats

    def request_gpu_session(self, hours: float, reason: str, requester: str = "admin") -> str:
        """
        Protokolliert GPU-Requests in KB und gibt eine request_id zurück.
        Admin-Workflow (Genehmigung) ist extern über Admin-Console umzusetzen.
        """
        if hours <= 0:
            raise ValueError("hours muss > 0 sein")
        req_id = str(uuid.uuid4())
        payload = {
            "request_id": req_id,
            "hours": float(hours),
            "reason": reason,
            "requester": requester,
            "status": "pending",
            "timestamp": int(time.time())
        }
        # Persist in knowledge base unter 'gpu_requests'
        self.kb.store("gpu_requests", str(payload))
        # cache in memory for quick lookup
        with self._lock:
            self._requests[req_id] = payload
        _LOGGER.info("GPU-Session angefragt: %s", payload)
        return req_id

    def list_gpu_requests(self) -> List[dict]:
        """Gibt alle angefragten GPU-Jobs (sowohl persisted als auch in-memory) zurück."""
        results = []
        # load from KB (gpu_requests) - KB returns strings; parse if needed
        rows = self.kb.search("gpu_requests")
        for r in rows:
            try:
                # attempt to eval safe-ish (it's human-readable dict), but avoid eval
                # stored as string(payload). We'll return as string if parsing not possible.
                results.append(r)
            except Exception:
                results.append(r)
        # also include in-memory
        with self._lock:
            for v in self._requests.values():
                results.append(v)
        return results
