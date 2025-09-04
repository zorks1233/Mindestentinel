# admin console 
# src/admin/admin_console.py
"""
Admin CLI für Mindestentinel.
- CLI mit einfachen Kommandos: status, list-models, start-api, register-plugin, request-gpu
- Designed for interactive local admin usage.
"""

from __future__ import annotations
import argparse
import logging
import os
import sys
import uvicorn
from typing import Optional

# Imports for core components
from src.core.model_manager import ModelManager
from src.modules.plugin_manager import PluginManager
from src.core.ai_engine import AIBrain
from src.api.rest_api import create_app
from src.api.websocket_api import create_ws_app

_LOG = logging.getLogger("mindestentinel.admin_console")
_LOG.addHandler(logging.NullHandler())

def build_core(rules_path: Optional[str] = None):
    mm = ModelManager()
    pm = PluginManager()
    brain = AIBrain(rules_path or os.path.join("config", "rules.yaml"))
    # inject model_manager into brain (multi orchestrator)
    brain.inject_model_manager(mm)
    return brain, mm, pm

def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="mindest-admin", description="Mindestentinel Admin Console")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Zeigt Systemstatus an")

    sub_list = sub.add_parser("list-models", help="Listet registrierte Modelle auf")

    sub_start_api = sub.add_parser("start-api", help="Startet REST API (uvicorn)")
    sub_start_api.add_argument("--host", default="0.0.0.0")
    sub_start_api.add_argument("--port", default=8000, type=int)
    sub_start_api.add_argument("--workers", default=1, type=int)

    reg = sub.add_parser("register-plugin", help="Registriert ein Plugin-Modul")
    reg.add_argument("name")
    reg.add_argument("module")

    req = sub.add_parser("request-gpu", help="Beantragt GPU-Session")
    req.add_argument("hours", type=float)
    req.add_argument("--reason", default="ad-hoc training")
    req.add_argument("--requester", default="admin")

    return p.parse_args(argv)

def cmd_status(brain: AIBrain):
    st = brain.status()
    print("Status:", st)

def cmd_list_models(mm: ModelManager):
    names = mm.list_models()
    print("Registered models:")
    for n in names:
        print(" -", n)
    print("Meta:", mm.info())

def cmd_start_api(brain: AIBrain, mm: ModelManager, pm: PluginManager, host: str, port: int, workers: int):
    app = create_app(brain, mm, pm)
    # start uvicorn programmatically (blocking)
    uvicorn.run(app, host=host, port=port, workers=workers)

def cmd_register_plugin(pm: PluginManager, mm: ModelManager, name: str, module: str):
    print(f"Register plugin {name} from module {module} ...")
    try:
        pm.register_plugin_from_module(module)
        # instantiate plugin in manager by importing module
        mod = __import__(module, fromlist=["*"])
        inst = None
        # try common class names
        for attr in ("Plugin", "ExternalModelPlugin", "VisionPlugin", "AudioPlugin"):
            if hasattr(mod, attr):
                cls = getattr(mod, attr)
                try:
                    inst = cls()
                    break
                except Exception:
                    continue
        if inst is None:
            inst = mod
        pm.register_plugin_instance(name, inst)
        mm.register_external_plugin(name, inst, default_model=None)
        print("Plugin registered.")
    except Exception as e:
        print("Error registering plugin:", e)

def cmd_request_gpu(brain: AIBrain, hours: float, reason: str, requester: str):
    rid = brain.request_gpu_session(hours, reason, requester)
    print("GPU request id:", rid)

def main(argv=None):
    args = parse_args(argv)
    brain, mm, pm = build_core()
    if args.cmd == "status":
        cmd_status(brain)
    elif args.cmd == "list-models":
        cmd_list_models(mm)
    elif args.cmd == "start-api":
        cmd_start_api(brain, mm, pm, args.host, args.port, args.workers)
    elif args.cmd == "register-plugin":
        cmd_register_plugin(pm, mm, args.name, args.module)
    elif args.cmd == "request-gpu":
        cmd_request_gpu(brain, args.hours, args.reason, args.requester)
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
