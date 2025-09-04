#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "${ROOT}/.venv/bin/activate" || true
export MIND_API_KEY="${MIND_API_KEY:-changeme}"
python -m src.main --start-rest --api-port 8000
