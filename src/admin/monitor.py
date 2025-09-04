# monitor 
# src/admin/monitor.py
"""
Simple monitor loop that logs system health, triggers alerts (console/log).
- Can be used in background or invoked once for diagnostics.
"""

from __future__ import annotations
import logging
import time
from typing import Optional
from src.core.system_monitor import SystemMonitor

_LOG = logging.getLogger("mindestentinel.monitor")
_LOG.addHandler(logging.NullHandler())

def run_monitor_loop(interval: int = 30, run_once: bool = False):
    monitor = SystemMonitor()
    _LOG.info("Monitor loop started with interval=%ds", interval)
    try:
        while True:
            snap = monitor.snapshot()
            _LOG.info("Monitor snapshot: cpu=%s mem=%s disk=%s", snap["cpu"], snap["memory"], snap["disk"])
            # simple alert heuristics
            if snap["cpu"] > 90 or snap["memory"] > 95 or snap["disk"] > 95:
                _LOG.warning("Critical resource usage detected: %s", snap)
            if run_once:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        _LOG.info("Monitor stopped by user")
