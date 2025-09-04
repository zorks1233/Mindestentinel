# quantum_computing 
# src/core/quantum_computing.py
"""
QuantumComputing - Wrapper für Qiskit & PennyLane.
- Prüft verfügbare Backends, bietet helper zum Ausführen einfacher Schaltungen.
- Abhängigkeiten optional; bei Fehlen wird eine verständliche Exception geworfen.
"""

from __future__ import annotations
import logging
from typing import Dict, Any

_LOGGER = logging.getLogger("mindestentinel.quantum")

try:
    from qiskit import QuantumCircuit, Aer, execute
    _HAS_QISKIT = True
except Exception:
    _HAS_QISKIT = False

try:
    import pennylane as qml
    from pennylane import numpy as np
    _HAS_PENNYLANE = True
except Exception:
    _HAS_PENNYLANE = False

class QuantumComputing:
    def __init__(self, provider: str = "qiskit"):
        self.provider = provider
        if provider == "qiskit" and not _HAS_QISKIT:
            raise RuntimeError("Qiskit nicht installiert. pip install qiskit")
        if provider == "pennylane" and not _HAS_PENNYLANE:
            raise RuntimeError("PennyLane nicht installiert. pip install pennylane")
        _LOGGER.info("QuantumComputing initialized with provider=%s", provider)

    def run_bell_pair_qiskit(self) -> Dict[str, int]:
        if not _HAS_QISKIT:
            raise RuntimeError("Qiskit nicht verfügbar")
        backend = Aer.get_backend("qasm_simulator")
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0,1)
        qc.measure([0,1],[0,1])
        job = execute(qc, backend=backend, shots=1024)
        result = job.result()
        counts = result.get_counts()
        return counts

    def pennylane_expectation(self) -> float:
        if not _HAS_PENNYLANE:
            raise RuntimeError("PennyLane nicht verfügbar")
        dev = qml.device("default.qubit", wires=2)
        @qml.qnode(dev)
        def circuit():
            qml.Hadamard(wires=0)
            qml.CNOT(wires=[0,1])
            return qml.expval(qml.PauliZ(0))
        return float(circuit())
