# system_monitor 
# src/core/system_monitor.py
"""
SystemMonitor - nimmt Snapshots von CPU/RAM/Disk und bietet einfache Historie.
Benutzt psutil (installiere psutil in requirements).
"""

from __future__ import annotations
import psutil
import time
from typing import Dict, Any, List

class SystemMonitor:
    def __init__(self, history_limit: int = 1024):
        self.history: List[Dict[str, Any]] = []
        self.history_limit = history_limit

    def snapshot(self) -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        snap = {
            "timestamp": int(time.time()),
            "cpu": cpu,
            "memory": mem.percent,
            "memory_available": mem.available,
            "disk": disk.percent
        }
        self.history.append(snap)
        if len(self.history) > self.history_limit:
            self.history.pop(0)
        return snap

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self.history)
