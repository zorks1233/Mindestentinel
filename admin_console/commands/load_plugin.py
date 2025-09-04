#!/usr/bin/env python3
# admin_console/commands/load_plugin.py
"""Lädt und registriert ein Plugin-Modul:
- registriert Plugin in PluginManager
- registriert Plugin als Modell-Adapter im ModelManager
Usage:
    python admin_console/commands/load_plugin.py --name myplugin --module plugins.my_plugin [--default-model MODEL]
"""

import argparse
import sys
from src.admin.admin_console import build_core

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Lädt ein Plugin-Modul und registriert es")
    p.add_argument("--name", required=True, help="Interner Name für das Plugin")
    p.add_argument("--module", required=True, help="Python Modulname, z.B. 'plugins.external_model_plugin'")
    p.add_argument("--default-model", required=False, help="Optional: Default-Modellname für den Plugin-Adapter")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    brain, mm, pm = build_core()
    try:
        pm.register_plugin_from_module(args.module)
        # Instantiate plugin (try common class names)
        mod = __import__(args.module, fromlist=["*"])
        inst = None
        for attr in ("Plugin", "ExternalModelPlugin", "VisionPlugin", "AudioPlugin"):
            if hasattr(mod, attr):
                cls = getattr(mod, attr)
                try:
                    inst = cls()
                    break
                except Exception:
                    continue
        if inst is None:
            # fallback: use module object itself
            inst = mod
        pm.register_plugin_instance(args.name, inst)
        mm.register_external_plugin(args.name, inst, default_model=args.default_model)
        print(f"Plugin '{args.name}' geladen und registriert (module={args.module}).")
    except Exception as e:
        print("Fehler beim Laden des Plugins:", e, file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
