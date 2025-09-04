# src/main.py
"""
Einstiegspunkt für Mindestentinel.
- Startet AIBrain, ModelManager, PluginManager
- CLI-Flags:
    --start-rest  : startet FastAPI REST API (uvicorn)
    --start-ws    : startet WebSocket API
    --no-start    : nur initialisiert (useful for interactive use)
    --api-host / --api-port
Beispiel:
    python src/main.py --start-rest --api-port 8000
"""

from __future__ import annotations
import argparse
import multiprocessing
import platform

import os
import logging
import uvicorn
from typing import Optional

from src.core.model_manager import ModelManager
from src.modules.plugin_manager import PluginManager
from src.core.ai_engine import AIBrain
from src.api.rest_api import create_app
from src.api.websocket_api import create_ws_app

_LOG = logging.getLogger("mindestentinel.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def build_components(rules_path: Optional[str] = None):
    mm = ModelManager()
    pm = PluginManager()
    brain = AIBrain(rules_path or os.path.join("config", "rules.yaml"))
    # inject model manager
    brain.inject_model_manager(mm)
    return brain, mm, pm

def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--start-rest", action="store_true", help="Start REST API (uvicorn)")
    p.add_argument("--start-ws", action="store_true", help="Start WebSocket API (uvicorn)")
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
    except Exception:
        pass
    brain, mm, pm = build_components()

    # load plugins from plugins/ directory by default
    try:
        loaded = pm.load_plugins_from_dir()
        _LOG.info("Plugins auto-loaded: %d", loaded)
    except Exception:
        _LOG.exception("Fehler beim Laden von Plugins")

    # start brain (background loop etc.)
    brain.start()

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
            brain.stop()

if __name__ == "__main__":
    try:
        multiprocessing.freeze_support()
    except Exception:
        pass
    main()
