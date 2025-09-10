@echo off
REM Mindestentinel CLI Starter
REM Version 2.0 - Einfache und robuste Implementierung

REM Prüfe, ob .venv existiert
if not exist ".venv" (
    echo Fehler: Virtuelle Umgebung nicht gefunden. Bitte führen Sie zuerst install.bat aus.
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
call .venv\Scripts\activate.bat

REM Setze PYTHONPATH auf das Projekt-Root (wichtig für Modul-Importe)
set PYTHONPATH=%CD%

REM Prüfe auf Befehle
if "%1"=="" (
    goto help
)

REM Behandle das "start"-Kommando
if "%1"=="start" (
    goto start_command
)

REM Behandle das "admin"-Kommando
if "%1"=="admin" (
    goto admin_command
)

REM Behandle das "help"-Kommando
if "%1"=="help" (
    goto help
)

REM Unbekannter Befehl
echo Unbekannter Befehl: %1
exit /b 1

:start_command
shift
set MAIN_ARGS=

:arg_loop
if "%1"=="" goto start_system

if "%1"=="--rest" (
    set MAIN_ARGS=%MAIN_ARGS% --start-rest
) else if "%1"=="--ws" (
    set MAIN_ARGS=%MAIN_ARGS% --start-ws
) else if "%1"=="--autonomy" (
    set MAIN_ARGS=%MAIN_ARGS% --enable-autonomy
) else if "%1"=="--port" (
    if not "%2"=="" (
        set MAIN_ARGS=%MAIN_ARGS% --api-port %2
        shift
    ) else (
        echo Fehler: --port erwartet einen Wert
        exit /b 1
    )
) else (
    set MAIN_ARGS=%MAIN_ARGS% %1
)

shift
goto arg_loop

:start_system
if not "%MAIN_ARGS%"=="" (
    echo Starte System mit Argumenten: %MAIN_ARGS%
    python -m src.main %MAIN_ARGS%
    exit /b %errorlevel%
) else (
    echo Starte System mit Standardargumenten
    python -m src.main --start-rest
    exit /b %errorlevel%
)

:admin_command
shift
if "%1"=="users" (
    goto admin_users
) else (
    echo Unbekannter Admin-Befehl: %1
    exit /b 1
)

:admin_users
shift
if "%1"=="create" (
    shift
    set PYTHONPATH=%CD%
    python admin_console\commands\manage_users.py create %*
    exit /b %errorlevel%
) else if "%1"=="list" (
    shift
    set PYTHONPATH=%CD%
    python admin_console\commands\manage_users.py list %*
    exit /b %errorlevel%
) else if "%1"=="delete" (
    shift
    set PYTHONPATH=%CD%
    python admin_console\commands\manage_users.py delete %*
    exit /b %errorlevel%
) else (
    set PYTHONPATH=%CD%
    python admin_console\commands\manage_users.py %*
    exit /b %errorlevel%
)

:help
echo Mindestentinel CLI
echo -----------------
echo Verwendung: mindest [command] [options]
echo.
echo Befehle:
echo   start      - Startet das System
echo   admin      - Verwaltet Benutzer und System
echo   help       - Zeigt diese Hilfe an
echo.
echo Beispiele:
echo   mindest start --rest --autonomy --port 8000
echo   mindest admin users create --username admin --password "secure123"
exit /b 0