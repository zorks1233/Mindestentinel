# src/modules/utils/performance.py
"""
Performance helpers: decorator zur Laufzeitmessung, Ressourcen-Snapshots via psutil.
"""

from __future__ import annotations
import time
from typing import Callable, Any, Dict
try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    _HAS_PSUTIL = False

def measure_time(fn: Callable[..., Any]):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = fn(*args, **kwargs)
        end = time.time()
        duration = end - start
        # optional: log via standard logging
        try:
            import logging
            logging.getLogger("mindestentinel.performance").info("%s took %.4fs", fn.__name__, duration)
        except Exception:
            pass
        return res
    return wrapper

def resource_snapshot() -> Dict[str, Any]:
    if not _HAS_PSUTIL:
        return {"psutil": False}
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    disk = psutil.disk_usage('/')
    return {
        "psutil": True,
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_available": mem.available,
        "disk_percent": disk.percent
    }
