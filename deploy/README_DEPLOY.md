# Mindestentinel — Deployment helper (auto-generated)

This folder contains helper files to set up a Python virtual environment and install required dependencies.

Quick steps (Linux/macOS):
```bash
cd <project-root>
bash deploy/install.sh
source .venv/bin/activate
uvicorn src.api:app --reload --port 8000
```

Quick steps (Windows CMD / PowerShell):
```cmd
cd <project-root>
deploy\install.bat
call .venv\Scripts\activate
uvicorn src.api:app --reload --port 8000
```

Notes:
- The requirements list includes ML libs (transformers, torch). For best performance and CUDA support, install the correct `torch` wheel for your platform from https://pytorch.org/get-started/locally/
- If you already have a virtualenv, just activate it and run `pip install -r deploy/requirements.txt`.
- After dependencies are installed, start the API with `uvicorn src.api:app --reload --port 8000`.
