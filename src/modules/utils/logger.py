# src/modules/utils/logger.py
"""
Logger-Setup helper. Nutzt Python's logging mit RotatingFileHandler.
Aufruf: configure_logger("mindestentinel", "logs/system.log")
"""

from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logger(name: str = "mindestentinel", log_file: str = "logs/system.log", level: int = logging.INFO, max_bytes: int = 10*1024*1024, backup_count: int = 5):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        fh = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger
