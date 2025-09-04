#!/usr/bin/env python3
# admin_console/commands/monitor_ai.py
"""Zeigt System-Snapshots des SystemMonitor an. Optionen:
    --once    : nur ein Snapshot und exit
    --loop N  : Intervall in Sekunden (Standard 30)
Usage:
    python admin_console/commands/monitor_ai.py --once
"""

import argparse
import time
from src.admin.admin_console import build_core

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Monitor AI System (SystemMonitor snapshots)")
    p.add_argument("--once", action="store_true", help="Einmaligen Snapshot ausgeben und beenden")
    p.add_argument("--loop", type=int, default=30, help="Wenn gesetzt: wiederholtes Monitoring im Intervall (Sekunden)")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    brain, mm, pm = build_core()
    monitor = brain.system_monitor
    if args.once:
        snap = monitor.snapshot()
        print("Snapshot:", snap)
        return
    try:
        while True:
            snap = monitor.snapshot()
            print("[snapshot]", snap)
            time.sleep(args.loop)
    except KeyboardInterrupt:
        print("Monitor gestoppt durch Nutzer.")

if __name__ == "__main__":
    main()
