# src/main.py
"""
Einstiegspunkt für Mindestentinel.
- Startet AIBrain, ModelManager, PluginManager
- CLI-Flags:
    --start-rest      : startet FastAPI REST API (uvicorn)
    --start-ws        : startet WebSocket API
    --enable-autonomy : aktiviert den autonomen Lernzyklus
    --no-start        : nur initialisiert (useful for interactive use)
    --api-host / --api-port
Beispiel:
    python src/main.py --start-rest --enable-autonomy --api-port 8000
"""

from __future__ import annotations
import argparse
import multiprocessing
import platform
import os
import logging
import uvicorn
from typing import Optional, Tuple

# NEU: Import des AutonomousLoop
from src.core.autonomous_loop import AutonomousLoop

from src.core.model_manager import ModelManager
from src.modules.plugin_manager import PluginManager
from src.core.ai_engine import AIBrain
from src.api.rest_api import create_app
from src.api.websocket_api import create_ws_app

_LOG = logging.getLogger("mindestentinel.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# GEÄNDERT: build_components gibt nun auch autonomous_loop zurück
def build_components(rules_path: Optional[str] = None) -> Tuple[AIBrain, ModelManager, PluginManager, AutonomousLoop]:
    mm = ModelManager()
    pm = PluginManager()
    brain = AIBrain(rules_path or os.path.join("config", "rules.yaml"))
    # inject model manager
    brain.inject_model_manager(mm)
    
    # NEU: Initialisiere den autonomen Lernzyklus
    _LOG.info("Initialisiere den autonomen Lernzyklus...")
    autonomous_loop = AutonomousLoop(
        ai_engine=brain,
        knowledge_base=brain.knowledge_base,
        model_orchestrator=brain.model_orchestrator,
        rule_engine=brain.rule_engine,
        protection_module=brain.protection_module,
        model_manager=mm,
        system_monitor=brain.system_monitor,
        config={
            "max_learning_cycles": 1000,
            "learning_interval_seconds": 1800,  # Alle 30 Minuten
            "min_confidence_threshold": 0.65,
            "max_resource_usage": 0.85
        }
    )
    
    return brain, mm, pm, autonomous_loop

def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--start-rest", action="store_true", help="Start REST API (uvicorn)")
    p.add_argument("--start-ws", action="store_true", help="Start WebSocket API (uvicorn)")
    # NEU: Option zum Aktivieren des autonomen Lernzyklus
    p.add_argument("--enable-autonomy", action="store_true", help="Aktiviert den autonomen Lernzyklus")
    p.add_argument("--api-host", default="0.0.0.0")
    p.add_argument("--api-port", default=8000, type=int)
    p.add_argument("--no-start", action="store_true", help="Init components but do not start any server")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    # Ensure multiprocessing start method is compatible on Windows
    try:
        if platform.system() == 'Windows':
            multiprocessing.set_start_method('spawn', force=True)
    except Exception as e:
        _LOG.warning(f"Multiprocessing-Startmethode konnte nicht gesetzt werden: {str(e)}")
    
    # GEÄNDERT: Jetzt mit 4 Rückgabewerten
    brain, mm, pm, autonomous_loop = build_components()

    # load plugins from plugins/ directory by default
    try:
        loaded = pm.load_plugins_from_dir()
        _LOG.info("Plugins auto-loaded: %d", loaded)
    except Exception:
        _LOG.exception("Fehler beim Laden von Plugins")

    # start brain (background loop etc.)
    brain.start()
    
    # NEU: Starte den autonomen Lernzyklus, wenn aktiviert
    if args.enable_autonomy:
        _LOG.info("Aktiviere autonomen Lernzyklus...")
        autonomous_loop.start()

    if args.no_start:
        _LOG.info("System initialisiert (no-start). AIBrain läuft im Hintergrund. Exit.")
        return

    if args.start_rest:
        app = create_app(brain, mm, pm)
        _LOG.info("Starting REST API on %s:%d", args.api_host, args.api_port)
        uvicorn.run(app, host=args.api_host, port=args.api_port)
    elif args.start_ws:
        app = create_ws_app(brain)
        _LOG.info("Starting WebSocket API on %s:%d", args.api_host, args.api_port)
        uvicorn.run(app, host=args.api_host, port=args.api_port)
    else:
        _LOG.info("No API selected. Running in background. Use --start-rest or --start-ws to start servers.")
        try:
            while True:
                # keep main thread alive while brain background runs
                import time
                time.sleep(3600)
        except KeyboardInterrupt:
            _LOG.info("Received KeyboardInterrupt. Shutting down.")
            # NEU: Stoppe auch den autonomen Lernzyklus
            if args.enable_autonomy:
                _LOG.info("Deaktiviere autonomen Lernzyklus...")
                autonomous_loop.stop()
            brain.stop()

if __name__ == "__main__":
    try:
        multiprocessing.freeze_support()
    except Exception:
        pass
    main()