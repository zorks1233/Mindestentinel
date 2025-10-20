#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r deploy/requirements.txt
echo "Dependencies installed. To start the API:"
echo "  source .venv/bin/activate"
echo "  uvicorn src.api:app --reload --port 8000"
