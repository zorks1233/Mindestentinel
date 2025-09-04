#!/usr/bin/env python3
# admin_console/commands/stop_model.py
"""Stoppt ein Modell via ModelManager.stop_model(name)
Usage:
    python admin_console/commands/stop_model.py --name <model_name>
"""

import argparse
import sys
from src.admin.admin_console import build_core

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Stoppt ein Modell im ModelManager")
    p.add_argument("--name", required=True, help="Name des zu stoppenden Modells")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    brain, mm, pm = build_core()
    try:
        mm.stop_model(args.name)
        print(f"Model '{args.name}' wurde gestoppt.")
    except KeyError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unbekannter Fehler: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
