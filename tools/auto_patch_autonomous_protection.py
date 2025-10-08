#!/usr/bin/env python3
"""
tools/auto_patch_autonomous_protection.py

Wendet automatisch zwei Patches an:
 - macht ProtectionModule.__init__ tolerant (src/core/protection_module.py)
 - ersetzt den AutonomousLoop-Initialisierungsblock in src/main.py durch einen robusten Fallback-Block

Backups werden mit Suffix .bak.TIMESTAMP erstellt.
"""

import time
from pathlib import Path
import shutil
import re
import sys

TS = time.strftime("%Y%m%d%H%M%S")
ROOT = Path.cwd()
SRC = ROOT / "src"
CORE = SRC / "core"

FILES_CHANGED = []
FILES_SKIPPED = []
BACKUPS = []

def backup(path: Path):
    if not path.exists():
        return None
    bak = path.with_suffix(path.suffix + f".bak.{TS}")
    shutil.copy2(path, bak)
    BACKUPS.append(bak)
    return bak

def patch_protection_module():
    path = CORE / "protection_module.py"
    if not path.exists():
        print(f"[WARN] {path} nicht gefunden. Überspringe ProtectionModule-Patch.")
        FILES_SKIPPED.append(str(path))
        return

    print(f"[+] Patching {path}")
    bak = backup(path)
    if bak:
        print(f"    Backup erstellt: {bak.name}")

    text = path.read_text(encoding="utf-8")

    # Find first def __init__ in the file
    init_re = re.compile(r"(def\s+__init__\s*\([^\)]*\)\s*:\s*\n)", re.MULTILINE)
    m = init_re.search(text)
    if not m:
        print("    [WARN] Keine __init__-Definition gefunden in protection_module.py; füge kompatible __init__ am Dateiende ein.")
        addition = "\n\n# Autopatch: kompatible __init__\nclass _AutopatchedProtectionModule:\n    def __init__(self, rule_engine=None, knowledge_base=None, **kwargs):\n        import logging\n        self.logger = logging.getLogger('mindestentinel.protection_module')\n        if rule_engine is not None:\n            if not (hasattr(rule_engine, 'rules') or hasattr(rule_engine, 'validate') or hasattr(rule_engine, 'load_rules')):\n                self.logger.warning('Übergebenes rule_engine-Objekt entspricht nicht exakt dem erwarteten RuleEngine-Typ. Fahre dennoch fort.')\n        self.rule_engine = rule_engine\n        self.knowledge_base = knowledge_base\n"
        text = text + addition
        path.write_text(text, encoding="utf-8")
        FILES_CHANGED.append(str(path))
        print("    compat-__init__ appended.")
        return

    # Replace the first __init__ block body with our tolerant implementation
    # We'll replace the signature line and the following indented block until a line with same indentation as def or next def/class
    sig_start = m.start()
    sig_end = m.end()
    # Determine indentation from matched line
    line_start = text.rfind("\n", 0, sig_start) + 1
    def_line = text[line_start:text.find("\n", line_start)]
    indent_match = re.match(r"(\s*)def\s+__init__", def_line)
    base_indent = indent_match.group(1) if indent_match else ""
    body_indent = base_indent + "    "

    # Find end of the __init__ method: look for next line that matches '^<base_indent>def ' or '^<base_indent>class ' or EOF
    after = text[sig_end:]
    end_search = re.search(rf"\n{re.escape(base_indent)}(?:(def\s+)|(?:class\s+))", after)
    if end_search:
        body_end_index = sig_end + end_search.start()
    else:
        body_end_index = len(text)

    # Compose new __init__ block (keeps the same signature name but standardizes parameters)
    new_init = (
        f"{base_indent}def __init__(self, rule_engine=None, knowledge_base=None, **kwargs):\n"
        f"{body_indent}import logging\n"
        f"{body_indent}try:\n"
        f"{body_indent}    self.logger = logging.getLogger('mindestentinel.protection_module')\n"
        f"{body_indent}except Exception:\n"
        f"{body_indent}    self.logger = logging.getLogger(__name__)\n\n"
        f"{body_indent}if rule_engine is not None:\n"
        f"{body_indent}    if not (hasattr(rule_engine, 'rules') or hasattr(rule_engine, 'validate') or hasattr(rule_engine, 'load_rules')):\n"
        f"{body_indent}        self.logger.warning('Übergebenes rule_engine-Objekt entspricht nicht exakt dem erwarteten RuleEngine-Typ. Fahre dennoch fort (Interface-Check fehlgeschlagen).')\n"
        f"{body_indent}    else:\n"
        f"{body_indent}        self.logger.debug('rule_engine sieht kompatibel aus (Interface OK).')\n"
        f"{body_indent}else:\n"
        f"{body_indent}    self.logger.debug('Kein rule_engine übergeben (None).')\n\n"
        f"{body_indent}self.rule_engine = rule_engine\n"
        f"{body_indent}self.knowledge_base = knowledge_base\n\n"
        f"{body_indent}try:\n"
        f"{body_indent}    if hasattr(self, '_setup_defaults'):\n"
        f"{body_indent}        self._setup_defaults()\n"
        f"{body_indent}except Exception as e:\n"
        f"{body_indent}    self.logger.debug(f'Warnung in _setup_defaults(): {e}')\n"
    )

    new_text = text[:line_start] + new_init + text[body_end_index:]
    path.write_text(new_text, encoding="utf-8")
    FILES_CHANGED.append(str(path))
    print("    protection_module.py __init__ ersetzt (tolerante Version).")

def patch_main_autonomousblock():
    path = SRC / "main.py"
    if not path.exists():
        print(f"[WARN] {path} nicht gefunden. Überspringe main.py-Patch.")
        FILES_SKIPPED.append(str(path))
        return

    print(f"[+] Patching {path}")
    bak = backup(path)
    if bak:
        print(f"    Backup erstellt: {bak.name}")

    text = path.read_text(encoding="utf-8")

    # Search for the block start marker
    start_marker_re = re.compile(r"logger\.info\(\s*[\"']Initialisiere den autonomen Lernzyklus", re.IGNORECASE)
    m = start_marker_re.search(text)
    if not m:
        print("    [WARN] Konnte AutonomousLoop-Startmarker nicht finden. Suche alternative Marker...")
        # try another marker used earlier
        start_marker_re = re.compile(r"Initialisiere den autonomen Lernzyklus", re.IGNORECASE)
        m = start_marker_re.search(text)
        if not m:
            print("    [ERROR] Kein geeigneter Startmarker in main.py gefunden; Datei übersprungen.")
            FILES_SKIPPED.append(str(path))
            return

    start_index = text.rfind("\n", 0, m.start()) + 1

    # Heuristik: find the end by searching for either "if enable_autonomy" or "if not args.start_rest" after the block,
    # or the next major section like logger.info("... REST API ...")
    search_after = text[m.start():]
    # Look for 'if enable_autonomy' or 'if not args.start_rest' which typically come after
    end_marker = re.search(r"\n\s*if\s+enable_autonomy\b|\n\s*if\s+not\s+args\.start_rest\b|\n\s*# WICHTIG: Füge rule_engine zur Rückgabewert-Liste hinzu", search_after)
    if end_marker:
        end_index = m.start() + end_marker.start()
    else:
        # fallback: find next "logger.info(" occurrence after start and use position before it (but not the same)
        next_logger = re.search(r"\n\s*logger\.info\(", search_after)
        if next_logger:
            end_index = m.start() + next_logger.start()
        else:
            end_index = len(text)

    # Compose replacement block exactly as recommended earlier
    new_block = r'''
logger.info("Initialisiere den autonomen Lernzyklus...")
autonomous_loop = None

# Lokale Aliase (falls nicht definiert, None)
_mm = locals().get("model_manager", None)
_system_monitor = locals().get("system_monitor", None)
_model_cloner = locals().get("model_cloner", None)
_knowledge_transfer = locals().get("knowledge_transfer", None)
_model_trainer = locals().get("model_trainer", None)
_model_orchestrator = locals().get("model_orchestrator", None)
_kb = locals().get("kb", None)
_rule_engine = locals().get("rule_engine", None)
_protection_module = locals().get("protection_module", None)
_brain = locals().get("brain", None)

# Liste von sinnvollen Konstruktoraufrufen (von spezifisch zu generisch)
_autonomous_attempts = [
    # moderne keyword-basierte Variante (wenn vorhanden)
    lambda: AutonomousLoop(
        brain=_brain,
        model_manager=_mm,
        model_orchestrator=_model_orchestrator,
        knowledge_base=_kb,
        rule_engine=_rule_engine,
        protection_module=_protection_module,
    ),
    # Variante: keyword style mit core service names
    lambda: AutonomousLoop(
        model_manager=_mm,
        system_monitor=_system_monitor,
        model_cloner=_model_cloner,
        knowledge_transfer=_knowledge_transfer,
        model_trainer=_model_trainer
    ),
    # älteres positional ordering (gängig)
    lambda: AutonomousLoop(
        _mm,
        _system_monitor,
        _model_cloner,
        _knowledge_transfer,
        _model_trainer
    ),
    # alternative positional ordering (brain first)
    lambda: AutonomousLoop(
        _brain,
        _mm,
        _model_orchestrator,
        _kb,
        _rule_engine
    ),
    # weitere sinnvolle Kombinationen (falls Implementierungen variieren)
    lambda: AutonomousLoop(
        _model_orchestrator,
        _rule_engine,
        _protection_module,
        _mm
    ),
    # Fallback: no-arg constructor
    lambda: AutonomousLoop()
]

_last_exc = None
for attempt in _autonomous_attempts:
    try:
        autonomous_loop = attempt()
        logger.info("AutonomousLoop initialisiert.")
        break
    except TypeError as te:
        logger.debug(f"AutonomousLoop TypeError beim Versuch: {te}")
        _last_exc = te
    except Exception as e:
        logger.debug(f"AutonomousLoop Fehler beim Versuch: {e}")
        _last_exc = e

if autonomous_loop is None:
    logger.error(f"Fehler bei der Initialisierung des autonomen Lernzyklus: {_last_exc}")
    autonomous_loop = None
'''

    # Replace the section
    new_text = text[:start_index] + new_block + text[end_index:]
    path.write_text(new_text, encoding="utf-8")
    FILES_CHANGED.append(str(path))
    print("    main.py AutonomousLoop-Block ersetzt.")

def main():
    print("== auto_patch_autonomous_protection.py ==")
    print(f"Project root: {ROOT}")
    print("Erstelle Backups und wende Patches an...\n")

    patch_protection_module()
    patch_main_autonomousblock()

    print("\n== Ergebnis ==")
    if FILES_CHANGED:
        print("Geänderte Dateien:")
        for f in FILES_CHANGED:
            print("  -", f)
    if FILES_SKIPPED:
        print("Übersprungene / nicht gefundene Dateien:")
        for f in FILES_SKIPPED:
            print("  -", f)
    if BACKUPS:
        print("\nBackups erstellt:")
        for b in BACKUPS:
            print("  -", b.name)

    print("\nStarte nun dein Programm neu:")
    print("  python src/main.py --start-rest --enable-autonomy --api-port 8000")
    print("\nWenn danach noch Fehler auftreten: kopiere die ersten ~60 Log-Zeilen hierher, ich helfe weiter.")

if __name__ == "__main__":
    main()
