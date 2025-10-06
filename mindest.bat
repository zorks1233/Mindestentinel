@echo off
REM Mindestentinel - Alpha-Projekt Batch-Datei
REM Diese Datei startet das Mindestentinel-System mit allen Optionen

REM Überprüfe, ob das virtuelle Python-Environment existiert
if not exist ".venv" (
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
if not exist "requirements.txt" (
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

REM Setze PYTHONPATH auf das Projekt-Root und src-Verzeichnis
set PYTHONPATH=%CD%;%CD%\src

REM Prüfe, ob es sich um einen Admin-Befehl handelt
if "%1"=="admin" (
    REM Spezialbehandlung für Admin-Befehle
    if "%2"=="users" (
        REM Setze den richtigen PYTHONPATH für den UserManager
        set PYTHONPATH=%CD%;%CD%\src;%CD%\admin_console\commands
        REM Führe den UserManager direkt aus
        python -c "import sys, os; sys.path.insert(0, os.path.abspath('%CD%\src\core')); from src.core.user_manager import handle_admin_commands; sys.exit(0 if handle_admin_commands(sys.argv[2:]) else 1)" %*
        exit /b %errorlevel%
    ) else (
        REM Generische Behandlung für andere Admin-Befehle
        set PYTHONPATH=%CD%;%CD%\src;%CD%\admin_console\commands
        REM Führe den Befehl direkt aus
        python admin_console\commands\%2.py %3 %4 %5 %6 %7 %8 %9
        exit /b %errorlevel%
    )
)

REM Prüfe, ob es sich um einen Tool-Befehl handelt
if "%1"=="tool" (
    REM Setze den richtigen PYTHONPATH für Tools
    set PYTHONPATH=%CD%;%CD%\src
    REM Führe das Tool direkt aus
    python tools\%2.py %3 %4 %5 %6 %7 %8 %9
    exit /b %errorlevel%
)

REM Prüfe, ob es sich um einen Test-Befehl handelt
if "%1"=="test" (
    REM Setze den richtigen PYTHONPATH für Tests
    set PYTHONPATH=%CD%;%CD%\src
    REM Führe den Test direkt aus
    python tests\%2.py %3 %4 %5 %6 %7 %8 %9
    exit /b %errorlevel%
)

REM Prüfe, ob es sich um ein Plugin handelt
if "%1"=="plugin" (
    REM Setze den richtigen PYTHONPATH für Plugins
    set PYTHONPATH=%CD%;%CD%\src;%CD%\plugins
    REM Führe das Plugin direkt aus
    python plugins\%2.py %3 %4 %5 %6 %7 %8 %9
    exit /b %errorlevel%
)

REM Prüfe, ob es sich um einen API-Befehl handelt
if "%1"=="api" (
    REM Setze den richtigen PYTHONPATH für die API
    set PYTHONPATH=%CD%;%CD%\src
    REM Führe den API-Befehl direkt aus
    python api\%2.py %3 %4 %5 %6 %7 %8 %9
    exit /b %errorlevel%
)

REM Standardverhalten: Starte das Hauptsystem
set PYTHONPATH=%CD%;%CD%\src
python src/main.py %*