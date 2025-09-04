# cognitive_core 
# src/core/cognitive_core.py
"""
CognitiveCore - Lightweight neuron-like structure with plasticity.
- Not a full neural simulator, but capable of:
  - growing number of neurons
  - storing weighted connections
  - simple activation & Hebbian-style update
- All state can be serialized with to_dict()/from_dict()
"""

from __future__ import annotations
import math
import threading
import time
from typing import Dict, Any, Tuple

class CognitiveCore:
    def __init__(self):
        self._lock = threading.RLock()
        self.neurons: Dict[int, Dict[str, Any]] = {}  # id -> {bias, activation}
        self.connections: Dict[Tuple[int,int], float] = {}  # (src,dst) -> weight
        self._next_id = 0
        self.metadata = {"created": int(time.time())}

    def add_neuron(self, bias: float = 0.0) -> int:
        with self._lock:
            nid = self._next_id
            self.neurons[nid] = {"bias": float(bias), "activation": 0.0}
            self._next_id += 1
            return nid

    def connect(self, src: int, dst: int, weight: float = 0.01) -> None:
        with self._lock:
            if src not in self.neurons or dst not in self.neurons:
                raise KeyError("Neuron id nicht vorhanden")
            self.connections[(src, dst)] = float(weight)

    def activate(self, inputs: Dict[int, float]) -> Dict[int, float]:
        """
        inputs: neuron_id -> input_value
        returns activations after a simple weighted sum + tanh
        """
        with self._lock:
            # apply external inputs
            for nid, val in inputs.items():
                if nid in self.neurons:
                    self.neurons[nid]["activation"] = float(val)
            # compute propagation
            new_acts = {}
            for dst in self.neurons:
                s = 0.0
                for (src, d), w in self.connections.items():
                    if d == dst:
                        s += self.neurons[src]["activation"] * w
                s += self.neurons[dst]["bias"]
                act = math.tanh(s)
                new_acts[dst] = act
            # update activations
            for nid, act in new_acts.items():
                self.neurons[nid]["activation"] = act
            return new_acts

    def hebbian_update(self, learning_rate: float = 0.001):
        """Simple Hebbian rule: increase weights for co-activated neurons."""
        with self._lock:
            for (src, dst), w in list(self.connections.items()):
                a_src = self.neurons[src]["activation"]
                a_dst = self.neurons[dst]["activation"]
                dw = learning_rate * a_src * a_dst
                self.connections[(src, dst)] = float(w + dw)

    def to_dict(self) -> Dict[str, Any]:
        return {"neurons": self.neurons, "connections": self.connections, "meta": self.metadata}

    def from_dict(self, d: Dict[str, Any]) -> None:
        with self._lock:
            self.neurons = d.get("neurons", {})
            self.connections = {tuple(map(int, k.split(","))) if isinstance(k, str) else tuple(k): v for k,v in d.get("connections", {}).items()}
            self.metadata = d.get("meta", {})
