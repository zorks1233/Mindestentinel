#!/usr/bin/env bash
set -euo pipefail

# scripts/setup_and_run.sh
# Usage:
#   bash scripts/setup_and_run.sh [--install-reqs] [--apply-patches] [--test] [--start] [--detach] [--port PORT]
#
# Examples:
#   bash scripts/setup_and_run.sh --install-reqs --test --start
#   bash scripts/setup_and_run.sh --install-reqs --apply-patches --start --port 8000 --detach

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
REQ_FILE="${ROOT_DIR}/requirements.txt"
ENV_FILE="${ROOT_DIR}/.env"
PORT=8000
INSTALL_REQS=false
APPLY_PATCHES=false
RUN_TESTS=false
DO_START=false
DETACH=false

print_help() {
  cat <<EOF
Usage: $0 [--install-reqs] [--apply-patches] [--test] [--start] [--detach] [--port PORT]
  --install-reqs   Install dependencies (requirements.txt if present; otherwise minimal set)
  --apply-patches  If a patches/ folder with .patch files exist, try to apply them (git apply / patch)
  --test           Run syntax-check and unit tests (python -m compileall; python -m unittest ...)
  --start          Start REST API server (python src/main.py --start-rest --api-port PORT)
  --detach         Start server in background (nohup) - only valid with --start
  --port PORT      Port for API (default: 8000)
EOF
}

# parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-reqs) INSTALL_REQS=true; shift ;;
    --apply-patches) APPLY_PATCHES=true; shift ;;
    --test) RUN_TESTS=true; shift ;;
    --start) DO_START=true; shift ;;
    --detach) DETACH=true; shift ;;
    --port) PORT="$2"; shift 2 ;;
    -h|--help) print_help; exit 0 ;;
    *) echo "Unknown arg: $1"; print_help; exit 2 ;;
  esac
done

echo "Working in project root: ${ROOT_DIR}"
cd "${ROOT_DIR}"

# 1) Ensure python binary exists (prefer python3.13 if available)
PYTHON_CMD=""
for p in python3.13 python3 python; do
  if command -v "${p}" >/dev/null 2>&1; then
    PYTHON_CMD="${p}"
    break
  fi
done

if [[ -z "${PYTHON_CMD}" ]]; then
  echo "Python not found (need python 3.12+). Install Python and retry."
  exit 1
fi
echo "Using Python: ${PYTHON_CMD} ($( ${PYTHON_CMD} --version 2>&1 ))"

# 2) Create venv
if [[ ! -d "${VENV_DIR}" ]]; then
  echo "Creating virtualenv in ${VENV_DIR}..."
  ${PYTHON_CMD} -m venv "${VENV_DIR}"
else
  echo "Virtualenv exists: ${VENV_DIR}"
fi

# Activate venv for script-run
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

# 3) Install requirements if requested
if [[ "${INSTALL_REQS}" == "true" ]]; then
  if [[ -f "${REQ_FILE}" ]]; then
    echo "Installing requirements from ${REQ_FILE}..."
    pip install --upgrade pip wheel setuptools
    pip install -r "${REQ_FILE}"
  else
    echo "No requirements.txt found. Installing minimal runtime dependencies..."
    pip install --upgrade pip wheel setuptools
    pip install fastapi "uvicorn[standard]" python-multipart pyyaml numpy requests
  fi
fi

# 4) Generate MIND_API_KEY and write .env if not exists
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Generating new MIND_API_KEY and writing to ${ENV_FILE}..."
  NEW_KEY="$(${PYTHON_CMD} -c 'import secrets; print(secrets.token_urlsafe(48))')"
  cat > "${ENV_FILE}" <<EOF
# Auto-generated .env by scripts/setup_and_run.sh
MIND_API_KEY=${NEW_KEY}
EOF
  echo ".env created. (Don't commit this file.)"
else
  echo ".env file already exists; using existing environment variables from ${ENV_FILE}"
fi

# 4b) load .env into current shell (only for this script run)
if command -v dotenv >/dev/null 2>&1; then
  # if python-dotenv installed
  python - <<PY -c
from dotenv import load_dotenv
load_dotenv('${ENV_FILE}')
PY
else
  # simple loader for KEY=VALUE lines
  set -o allexport
  # shellcheck disable=SC1090
  [ -f "${ENV_FILE}" ] && source "${ENV_FILE}"
  set +o allexport
fi

if [[ -z "${MIND_API_KEY:-}" ]]; then
  echo "ERROR: MIND_API_KEY environment variable not set after loading ${ENV_FILE}."
  exit 1
fi
echo "MIND_API_KEY is set for this session (hidden)."

# 5) Apply patches if requested
if [[ "${APPLY_PATCHES}" == "true" ]]; then
  PATCH_DIR="${ROOT_DIR}/patches"
  if [[ -d "${PATCH_DIR}" ]]; then
    shopt -s nullglob
    PATCH_FILES=("${PATCH_DIR}"/*.patch)
    if [[ ${#PATCH_FILES[@]} -gt 0 ]]; then
      echo "Found ${#PATCH_FILES[@]} patch files; attempting to apply..."
      for pf in "${PATCH_FILES[@]}"; do
        echo "Applying patch: ${pf}"
        if command -v git >/dev/null 2>&1; then
          git apply "${pf}" || { echo "git apply failed for ${pf}, trying patch -p0..."; patch -p0 < "${pf}" || { echo "Failed to apply ${pf}"; exit 1; }; }
        elif command -v patch >/dev/null 2>&1; then
          patch -p0 < "${pf}" || { echo "Failed to apply ${pf}"; exit 1; }
        else
          echo "Neither git nor patch available; cannot apply ${pf}"
          exit 1
        fi
      done
      echo "Patches applied."
    else
      echo "No .patch files in ${PATCH_DIR}."
    fi
    shopt -u nullglob
  else
    echo "No patches directory found at ${PATCH_DIR} — skipping patch step."
  fi
fi

# 6) Syntax check (compileall)
echo "Running syntax check (compileall)..."
${PYTHON_CMD} -m compileall -q .

# 7) Run tests if requested
if [[ "${RUN_TESTS}" == "true" ]]; then
  echo "Running unit tests..."
  set +e
  ${PYTHON_CMD} -m unittest discover -s tests -v
  TEST_RET=$?
  set -e
  if [[ ${TEST_RET} -ne 0 ]]; then
    echo "Some tests failed (exit ${TEST_RET}). Review output above."
  else
    echo "All tests passed."
  fi
fi

# 8) Start server if requested
if [[ "${DO_START}" == "true" ]]; then
  if [[ "${DETACH}" == "true" ]]; then
    LOGFILE="${ROOT_DIR}/logs/server.out"
    mkdir -p "$(dirname "${LOGFILE}")"
    echo "Starting server in background (nohup). Log -> ${LOGFILE}"
    nohup ${PYTHON_CMD} src/main.py --start-rest --api-port "${PORT}" > "${LOGFILE}" 2>&1 &
    echo "Server started (background). Use 'tail -f ${LOGFILE}' to view logs."
  else
    echo "Starting server in foreground on port ${PORT}..."
    exec ${PYTHON_CMD} src/main.py --start-rest --api-port "${PORT}"
  fi
else
  echo "Setup complete. To start the server run:"
  echo "  source .venv/bin/activate"
  echo "  python src/main.py --start-rest --api-port ${PORT}"
fi
