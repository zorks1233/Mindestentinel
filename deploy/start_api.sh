#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate || (echo "Activate your venv first"; exit 1)
echo "Running quick status check..."
python -m src.main --status
echo "Starting uvicorn..."
uvicorn src.api:app --reload --port 8000
