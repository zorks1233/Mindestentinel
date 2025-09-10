@echo off
REM Mindestentinel Installationsskript für Windows
REM Version 1.0

echo Mindestentinel Installation
echo -------------------------

REM Prüfe Python-Version
python --version | findstr /C:"Python 3" >nul
if %errorlevel% neq 0 (
    echo Fehler: Python 3.x wird benötigt
    echo Bitte installieren Sie Python 3.10 oder neuer von https://python.org
    pause
    exit /b 1
)

REM Erstelle virtuelle Umgebung
echo Erstelle virtuelle Umgebung...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Fehler bei der Erstellung der virtuellen Umgebung
    pause
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
echo Aktiviere virtuelle Umgebung...
call .venv\Scripts\activate.bat

REM Installiere Abhängigkeiten
echo Installiere Abhängigkeiten...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Fehler bei der Installation der Abhängigkeiten
    pause
    exit /b 1
)

REM Erstelle benötigte Verzeichnisse
echo Erstelle benötigte Verzeichnisse...
if not exist "data\knowledge" mkdir data\knowledge
if not exist "data\models" mkdir data\models
if not exist "config" mkdir config

REM Signiere Regeldatei, falls nicht vorhanden
if not exist "config\rules.sig" (
    echo Signiere Regeldatei...
    python scripts\sign_rules.py config\rules.json
)

REM Erstelle .env-Datei, falls nicht vorhanden
if not exist ".env" (
    echo Erstelle .env-Datei...
    echo MIND_API_KEY=%RANDOM%%RANDOM%%RANDOM% > .env
    echo # API-Schlüssel für externe Dienste >> .env
    echo # OLLAMA_API_BASE=http://localhost:11434 >> .env
    echo # HUGGINGFACE_TOKEN=mein_token >> .env
)

REM Installation abgeschlossen
echo.
echo Installation abgeschlossen!
echo.
echo So starten Sie das System:
echo   mindest.bat start --rest --autonomy
echo.
echo So starten Sie die Admin-Konsole:
echo   mindest.bat admin help
echo.
echo Drücken Sie eine beliebige Taste, um dieses Fenster zu schließen...
pause >nul