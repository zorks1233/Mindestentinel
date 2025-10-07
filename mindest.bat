@echo off
REM Mindestentinel CLI Starter - Garantiert funktionierend
REM Diese Datei startet das System mit korrektem PYTHONPATH

REM Prüfe, ob .venv existiert
if not exist ".venv" (
    echo Fehler: Virtuelle Umgebung nicht gefunden. Bitte fuehren Sie zuerst install.bat aus.
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
call .venv\Scripts\activate.bat

REM Setze PYTHONPATH auf das Projekt-Root (WICHTIG!)
set PYTHONPATH=%CD%

REM Starte das System mit den übergebenen Argumenten
python -m src.main %*

REM Deaktiviere das virtuelle Environment (optional)
REM call .venv\Scripts\deactivate.bat