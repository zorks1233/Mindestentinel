# quantum_run 
#!/usr/bin/env python3
"""
Run a small quantum demo if qiskit/pennylane installed.
"""
from src.core.quantum_core import QuantumCore

def main():
    qc = QuantumCore(provider="qiskit")
    res = qc.run_bell_pair()
    print("Bell counts:", res)

if __name__ == "__main__":
    main()
