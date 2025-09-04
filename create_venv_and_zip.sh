#!/usr/bin/env bash
# create_venv_and_zip.sh
# Usage: bash create_venv_and_zip.sh /path/to/project [--with-reqs]
# This script creates a Python venv at .venv and installs requirements (if requested),
# then creates a ZIP including .venv. Run locally on your machine where internet and Python are available.
set -euo pipefail
PROJ_DIR="${1:-.}"
WITH_REQS=false
if [[ "${2:-}" == "--with-reqs" ]]; then WITH_REQS=true; fi
cd "$PROJ_DIR"
PYTHON_CMD="python3.13"
if ! command -v $PYTHON_CMD >/dev/null 2>&1; then
  for p in python3 python; do
    if command -v $p >/dev/null 2>&1; then PYTHON_CMD=$p; break; fi
  done
fi
echo "Using $PYTHON_CMD"
$PYTHON_CMD -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
if [ "$WITH_REQS" = true ] && [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
deactivate
ZIP_NAME="$(basename "$PWD")-with-venv.zip"
echo "Creating zip: $ZIP_NAME (this can be large)"
zip -r "../$ZIP_NAME" . -x "*.pyc" -x "__pycache__/*"
echo "Done. Zip created at ../$ZIP_NAME"
