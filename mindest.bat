@echo off
setlocal
cd /d "%~dp0"

REM Aktiviere virtuelle Umgebung
call .venv\Scripts\activate.bat

REM Setze PYTHONPATH
set PYTHONPATH=%CD%

REM Leite ALLE Argumente direkt an die main.py weiter
python -m src.main %*