"""
patch_multiprocessing.py
Patch für das multiprocessing-Modul in Python 3.13+
Fügt die fehlende set_start_method-Funktion hinzu
"""

import logging
import sys
import multiprocessing as mp

logger = logging.getLogger("mindestentinel.patch_multiprocessing")

# Prüfe, ob wir Python 3.13+ verwenden
if sys.version_info >= (3, 13):
    logger.info("Patche multiprocessing-Modul für Python 3.13+")
    
    # Prüfe, ob set_start_method bereits existiert
    if not hasattr(mp, 'set_start_method'):
        # Definiere eine leere set_start_method-Funktion
        def set_start_method(method, force=False):
            """Leere Funktion als Patch für Python 3.13+"""
            logger.debug(f"set_start_method({method}, {force}) aufgerufen (Patch)")
            pass
        
        # Füge die Funktion zum Modul hinzu
        mp.set_start_method = set_start_method
        logger.debug("set_start_method erfolgreich gepatcht")
else:
    logger.debug("Kein Patch für multiprocessing nötig (Python < 3.13)")