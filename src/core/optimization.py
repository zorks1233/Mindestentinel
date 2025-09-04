# src/core/optimization.py
"""
Optimization - Lightweight parameter tracking & simple search suggestions.
- Keine Blackbox-Optimierung; liefert Empfehlungen und hält Metriken.
- Integration: KnowledgeBase kann Metriken ablegen.
"""

from __future__ import annotations
import time
import math
from typing import Dict, Any, Optional

class Optimization:
    def __init__(self):
        self.history: list[Dict[str, Any]] = []

    def record(self, metric_name: str, value: float, meta: Optional[Dict[str,Any]] = None) -> None:
        entry = {"metric": metric_name, "value": float(value), "meta": meta or {}, "ts": int(time.time())}
        self.history.append(entry)

    def last(self, metric_name: str) -> Optional[Dict[str, Any]]:
        for e in reversed(self.history):
            if e["metric"] == metric_name:
                return e
        return None

    def suggest_parameter_adjustment(self, current_params: Dict[str, float], metric_name: str, target: float) -> Dict[str, float]:
        """
        Very simple heuristic:
        - if metric < target -> increase numeric params slightly
        - if metric > target -> decrease
        Returns new_params dict (not applied automatically).
        """
        last = self.last(metric_name)
        if last is None:
            # no data: small random-ish suggestion (deterministic)
            factor = 1.02
        else:
            diff = last["value"] - target
            # sigmoid scale for adjustments
            factor = 1.0 + (0.01 * -math.tanh(diff / max(abs(target), 1.0)))
        new_params = {}
        for k, v in current_params.items():
            if isinstance(v, (int, float)):
                new_params[k] = float(v) * factor
            else:
                new_params[k] = v
        return new_params
# optimization 
