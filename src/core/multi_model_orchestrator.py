# src/core/multi_model_orchestrator.py
"""
MultiModelOrchestrator - koordiniert parallele Abfragen an mehrere Modelle.
Erwartet einen model_manager mit Methoden:
- list_models() -> List[str]
- get_model(name) -> model_obj

Model-Interface (erwartet):
- async generate(prompt: str) -> str   OR
- generate_sync(prompt: str) -> str
"""

from __future__ import annotations
import asyncio
import logging
from typing import Dict, List, Optional

_LOGGER = logging.getLogger("mindestentinel.multi_orchestrator")
_LOGGER.addHandler(logging.NullHandler())

class MultiModelOrchestrator:
    def __init__(self, model_manager=None):
        self.model_manager = model_manager

    async def _call_model_async(self, model_name: str, prompt: str, timeout: float = 30.0) -> str:
        model = self.model_manager.get_model(model_name)
        if model is None:
            raise ValueError(f"Model '{model_name}' nicht gefunden")

        # prefer async generate if available
        if hasattr(model, "generate") and asyncio.iscoroutinefunction(model.generate):
            try:
                return await asyncio.wait_for(model.generate(prompt), timeout=timeout)
            except asyncio.TimeoutError:
                return f"[{model_name}] Timeout after {timeout}s"
        # fallback to e.g. generate_sync executed in thread
        elif hasattr(model, "generate_sync"):
            try:
                return await asyncio.wait_for(asyncio.to_thread(model.generate_sync, prompt), timeout=timeout)
            except asyncio.TimeoutError:
                return f"[{model_name}] Timeout after {timeout}s"
        else:
            raise TypeError(f"Model '{model_name}' hat keine kompatible generate-Methode")

    async def query_models_batch(self, model_names: List[str], prompt: str, timeout: float = 30.0) -> Dict[str, str]:
        """Fragt parallel mehrere Modelle ab und gibt Mapping name->response zurück."""
        if not self.model_manager:
            raise RuntimeError("model_manager nicht gesetzt in MultiModelOrchestrator")

        tasks = {}
        for name in model_names:
            tasks[name] = asyncio.create_task(self._call_model_async(name, prompt, timeout=timeout))

        results: Dict[str, str] = {}
        for name, task in tasks.items():
            try:
                res = await task
                results[name] = res
            except Exception as e:
                _LOGGER.exception("Fehler beim Abfragen von %s: %s", name, e)
                results[name] = f"[{name}] error: {e}"
        return results

    def list_models(self) -> List[str]:
        if not self.model_manager:
            return []
        return self.model_manager.list_models()
