@echo off
REM Mindestentinel CLI Starter

REM Prüfe, ob .venv existiert
if not exist ".venv" (
    echo Fehler: Virtuelle Umgebung nicht gefunden. Bitte führen Sie zuerst install.bat aus.
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
call .venv\Scripts\activate.bat

REM Prüfe auf Befehl
if "%1"=="" (
    echo Mindestentinel CLI
    echo -----------------
    echo Verwendung: mindest.bat [command] [options]
    echo.
    echo Befehle:
    echo   start      - Startet das System
    echo   admin      - Verwaltet Benutzer und System
    echo   help       - Zeigt diese Hilfe an
    echo.
    echo Beispiele:
    echo   mindest.bat start --rest --autonomy
    echo   mindest.bat admin users create --username admin --password "secure123"
    exit /b 0
)

REM Behandle Befehle
if "%1"=="start" (
    shift
    python -m src.main --start-rest %*
    exit /b %errorlevel%
)

if "%1"=="admin" (
    shift
    REM Prüfe auf Unterbefehl
    if "%1"=="users" (
        shift
        if "%1"=="create" (
            shift
            python admin_console\commands\manage_users.py create %*
        ) else if "%1"=="list" (
            shift
            python admin_console\commands\manage_users.py list %*
        ) else if "%1"=="delete" (
            shift
            python admin_console\commands\manage_users.py delete %*
        ) else (
            python admin_console\commands\manage_users.py %*
        )
    ) else (
        echo Unbekannter Admin-Befehl: %1
        exit /b 1
    )
    exit /b %errorlevel%
)

if "%1"=="help" (
    echo Mindestentinel CLI
    echo -----------------
    echo Verwendung: mindest.bat [command] [options]
    echo.
    echo Befehle:
    echo   start      - Startet das System
    echo   admin      - Verwaltet Benutzer und System
    echo   help       - Zeigt diese Hilfe an
    exit /b 0
)

echo Unbekannter Befehl: %1
exit /b 1