#!/usr/bin/env python3
# admin_console/commands/quantum_control.py
"""Steuert QuantumCore Operationen (falls verfügbar).
Options:
    --provider qiskit|pennylane
    --action info|bell|pennylane_expect
Usage:
    python admin_console/commands/quantum_control.py --provider qiskit --action bell
"""

import argparse
import sys
from src.admin.admin_console import build_core
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Quantum control helper")
    p.add_argument("--provider", default="qiskit", choices=["qiskit", "pennylane"], help="Welcher Quantum-Provider")
    p.add_argument("--action", default="info", choices=["info", "bell", "pennylane_expect"], help="Aktion")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    brain, mm, pm = build_core()
    try:
        from src.core.quantum_core import QuantumCore
    except Exception as e:
        print("QuantumCore nicht verfügbar:", e, file=sys.stderr)
        sys.exit(2)
    try:
        qc = QuantumCore(provider=args.provider)
        if args.action == "info":
            print(qc.provider_info())
        elif args.action == "bell":
            res = qc.run_bell_pair()
            print("Bell counts:", res)
        elif args.action == "pennylane_expect":
            val = qc.pennylane_expectation()
            print("PennyLane expectation sum:", val)
    except Exception as e:
        print("Fehler bei Quantum-Aktion:", e, file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
