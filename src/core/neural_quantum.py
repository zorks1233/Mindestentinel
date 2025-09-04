# neural_quantum 
# src/core/neural_quantum.py
"""
NeuralQuantumNet - PennyLane-basierter Hybrid-QNN-Baustein.
- leichte API: forward(params), loss_fn(params, data), update(params, grads)
- nutzt pennylane numpy (automatisch diff) falls vorhanden.
"""

from __future__ import annotations
import logging

_LOGGER = logging.getLogger("mindestentinel.neural_quantum")

try:
    import pennylane as qml
    from pennylane import numpy as np
    _HAS_PENNYLANE = True
except Exception:
    _HAS_PENNYLANE = False

class NeuralQuantumNet:
    def __init__(self, wires: int = 2):
        if not _HAS_PENNYLANE:
            raise RuntimeError("PennyLane nicht installiert (pip install pennylane).")
        self.wires = wires
        self.dev = qml.device("default.qubit", wires=wires)
        # initial params
        self.params = np.random.normal(0, 0.1, size=(wires,))
        _LOGGER.info("NeuralQuantumNet initialized with wires=%s", wires)

        @qml.qnode(self.dev)
        def _circuit(params):
            for i in range(self.wires):
                qml.RX(params[i], wires=i)
            if self.wires >= 2:
                qml.CNOT(wires=[0,1])
            return [qml.expval(qml.PauliZ(i)) for i in range(self.wires)]
        self._circuit = _circuit

    def forward(self, params = None):
        params = params if params is not None else self.params
        return self._circuit(params)

    def update_params(self, new_params):
        self.params = new_params
        return self.params
