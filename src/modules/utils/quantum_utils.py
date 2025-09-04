# src/modules/utils/quantum_utils.py
"""
Quantum utils: kleine Helfer zur Serialisierung von Qiskit-Ergebnissen
und zur Prüfung der Verfügbarkeit von Qiskit/PennyLane.
"""

from __future__ import annotations
from typing import Dict, Any

def provider_availability() -> Dict[str, bool]:
    info = {}
    try:
        import qiskit  # type: ignore
        info["qiskit"] = True
    except Exception:
        info["qiskit"] = False
    try:
        import pennylane as qml  # type: ignore
        info["pennylane"] = True
    except Exception:
        info["pennylane"] = False
    return info

def serialize_qiskit_counts(counts: Dict[str, int]) -> Dict[str, Any]:
    # counts from qiskit are already dict; return shaped info
    total = sum(counts.values()) if counts else 0
    return {"counts": counts, "total_shots": total}
