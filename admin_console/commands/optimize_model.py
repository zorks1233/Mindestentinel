#!/usr/bin/env python3
# admin_console/commands/optimize_model.py
"""Fordert eine Optimierungs-Routine an (SelfLearning.perform_optimization / Optimization)
Usage:
    python admin_console/commands/optimize_model.py [--print]
"""

import argparse
import json
from src.admin.admin_console import build_core
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Starte Optimierungs-Routine im System")
    p.add_argument("--print", action="store_true", help="Gebe das Ergebnis als JSON aus")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    brain, mm, pm = build_core()
    try:
        # Trigger perform_optimization in SelfLearning
        if hasattr(brain, "self_learning") and hasattr(brain.self_learning, "perform_optimization"):
            res = brain.self_learning.perform_optimization()
            print("Optimization result stored.")
            if args.print:
                print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            # Fallback: use Optimization module if available
            from src.core.optimization import Optimization
            opt = Optimization()
            opt.record("heartbeat", 1.0)
            print("Fallback-Optimization ausgeführt (minimal).")
    except Exception as e:
        print("Fehler bei der Optimierung:", e)

if __name__ == "__main__":
    main()
