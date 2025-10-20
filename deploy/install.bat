@echo off
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r deploy\requirements.txt
echo Dependencies installed. To start the API:
echo   call .venv\Scripts\activate
echo   uvicorn src.api:app --reload --port 8000
