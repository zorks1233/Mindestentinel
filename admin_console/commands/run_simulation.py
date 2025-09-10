#!/usr/bin/env python3
# admin_console/commands/run_simulation.py
"""Startet eine Simulation oder legt einen Task zur Simulation an.
Implementation (Alpha): legt einen Task 'run_simulation' in TaskManagement an.
Usage:
    python admin_console/commands/run_simulation.py [--priority N] [--description TEXT]
"""

import argparse
from src.admin.admin_console import build_core
from src.core.task_management import TaskManagement
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Triggert Simulation (legt Task in TaskManagement)")
    p.add_argument("--priority", type=int, default=0, help="Priorität der Simulation")
    p.add_argument("--description", default="run_simulation", help="Beschreibung des Tasks")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    brain, mm, pm = build_core()
    tm = TaskManagement()
    task_id = tm.add_task(args.description, priority=args.priority)
    print(f"Simulations-Task angelegt: id={task_id}, desc='{args.description}', priority={args.priority}")

if __name__ == "__main__":
    main()
