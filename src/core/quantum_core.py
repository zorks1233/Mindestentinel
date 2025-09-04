# quantum_core 
# src/core/quantum_core.py
"""
QuantumCore - höherstufige Fassade für Quanten-Operationen.
- Nutzt die bereits implementierten low-level Helfer (quantum_computing.py, neural_quantum.py)
- Wählt Provider (qiskit / pennylane) basierend auf Konfiguration oder Runtime
- Stellt sichere wrappers zur Verfügung, die Exceptions bei fehlenden Bibliotheken liefern
"""

from __future__ import annotations
from typing import Any, Dict, Optional
import logging

_LOGGER = logging.getLogger("mindestentinel.quantum_core")
_LOGGER.addHandler(logging.NullHandler())

# Import optional modules lazily to give clear errors
try:
    from src.core.quantum_computing import QuantumComputing  # may raise if qiskit missing
    _HAS_QCOMP = True
except Exception:
    QuantumComputing = None
    _HAS_QCOMP = False

try:
    from src.core.neural_quantum import NeuralQuantumNet
    _HAS_NQ = True
except Exception:
    NeuralQuantumNet = None
    _HAS_NQ = False

class QuantumCore:
    def __init__(self, provider: str = "qiskit"):
        self.provider = provider
        if provider == "qiskit" and not _HAS_QCOMP:
            raise RuntimeError("Qiskit (quantum_computing) ist nicht verfügbar. Installiere qiskit.")
        if provider == "pennylane" and not _HAS_NQ and not _HAS_QCOMP:
            raise RuntimeError("PennyLane / NeuralQuantum nicht verfügbar.")
        # instantiate provider-specific wrapper if available
        self._qc = None
        if _HAS_QCOMP:
            try:
                self._qc = QuantumComputing(provider=provider)
            except Exception as e:
                _LOGGER.warning("QuantumComputing konnte nicht initialisiert werden: %s", e)

    def run_bell_pair(self) -> Dict[str, int]:
        """Erstellt ein Bell-Pair mit Qiskit (falls verfügbar) und liefert Counts."""
        if not _HAS_QCOMP or not self._qc:
            raise RuntimeError("Qiskit backend nicht verfügbar.")
        return self._qc.run_bell_pair_qiskit()

    def pennylane_expectation(self) -> float:
        """Kleinere helper via PennyLane / neural quantum."""
        if not _HAS_NQ:
            raise RuntimeError("PennyLane-basierte Netze nicht verfügbar.")
        # instantiate a small NeuralQuantumNet and run forward
        nq = NeuralQuantumNet(wires=2)
        out = nq.forward()
        # convert output to float (sum of expectations)
        try:
            return float(sum(out))
        except Exception:
            return 0.0

    def provider_info(self) -> Dict[str, Any]:
        return {"provider": self.provider, "has_qcomp": _HAS_QCOMP, "has_neural_quantum": _HAS_NQ}
