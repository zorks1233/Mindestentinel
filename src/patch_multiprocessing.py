# src/patch_multiprocessing.py
"""
Dieses Modul behebt das Multiprocessing-Problem unter Windows mit PyCharm-Debugger.

WICHTIG: Diese Datei MUSS vor allen anderen Imports in main.py importiert werden!
"""

import os
import sys
import logging

logger = logging.getLogger("mindestentinel.patch_multiprocessing")


def apply_multiprocessing_patch():
    """Wendet die notwendigen Patches für Multiprocessing unter Windows an"""
    try:
        # Prüfe, ob wir unter Windows laufen
        is_windows = sys.platform == "win32"
        # Prüfe, ob der PyCharm-Debugger aktiv ist
        is_debugging = 'pydevd' in sys.modules or 'pdb' in sys.modules

        if is_windows and is_debugging:
            logger.info("Erkenne Windows mit aktiviertem PyCharm-Debugger. Wende spezielle Patches an...")

            # Deaktiviere das Multiprocessing-Patching des Debuggers
            os.environ["PYDEVDmultiprocess"] = "False"
            logger.info("Setze PYDEVDmultiprocess=False um Debugger-Konflikte zu vermeiden")

            # Stelle sicher, dass der Debugger keine Multiprocessing-Patches anwendet
            if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
                logger.info("Debugger-Trace-Funktion erkannt. Entferne Multiprocessing-Patches...")
                try:
                    import pydevd
                    # Deaktiviere explizit das Multiprocessing-Patching
                    pydevd.settrace(suspend=False, patch_multiprocessing=False)
                    logger.info("Deaktiviere Multiprocessing-Patching im Debugger")
                except ImportError:
                    logger.warning("Konnte pydevd nicht importieren. Debugger-Patching bleibt aktiv.")

        return True
    except Exception as e:
        logger.warning(f"Fehler beim Anwenden des Multiprocessing-Patches: {str(e)}")
        return False


# Führe den Patch sofort aus, wenn dieses Modul importiert wird
apply_multiprocessing_patch()
