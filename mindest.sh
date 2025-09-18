#!/bin/bash

# Wechsle in das Projektverzeichnis
cd "$(dirname "$0")"

# Aktiviere virtuelle Umgebung
source .venv/bin/activate

# Setze PYTHONPATH
export PYTHONPATH="$PWD"

# Leite alle Befehle direkt an die main.py weiter
python -m src.main "$@"