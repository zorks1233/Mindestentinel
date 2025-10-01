@echo off
REM Mindestentinel - Alpha-Projekt Batch-Datei
REM Diese Datei startet das Mindestentinel-System mit den gewünschten Optionen

REM Überprüfe, ob das virtuelle Python-Environment existiert
if not exist .venv (
    echo Erstelle virtuelles Python-Environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Fehler beim Erstellen des virtuellen Environments
        exit /b 1
    )
)

REM Aktiviere das virtuelle Environment
call .venv\Scripts\activate.bat

REM Installiere die Abhängigkeiten, falls nicht vorhanden
if not exist requirements.txt (
    echo Fehler: requirements.txt nicht gefunden
    exit /b 1
)

REM Überprüfe, ob alle benötigten Pakete installiert sind
python -c "import pkg_resources; pkg_resources.require(open('requirements.txt'))" >nul 2>&1
if errorlevel 1 (
    echo Installiere Abhängigkeiten...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Fehler bei der Installation der Abhängigkeiten
        exit /b 1
    )
)

REM Setze das PYTHONPATH, falls nicht gesetzt
if not defined PYTHONPATH (
    set PYTHONPATH=%CD%
)

REM Starte das System mit den übergebenen Argumenten
python src/main.py %*

REM Deaktiviere das virtuelle Environment (optional)
REM call .venv\Scripts\deactivate.bat