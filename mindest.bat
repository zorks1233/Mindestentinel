@echo off
REM Mindestentinel CLI Starter
REM Version 1.5 - Vollständig korrigiert für direkten Start

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
)

REM Behandle das "start"-Kommando
if "%1"=="start" (
    shift
    
    REM Initialisiere die Argumente für main.py
    set MAIN_ARGS=
    
    REM Verarbeite alle weiteren Argumente
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
)

:start_system
REM Starte das System mit den gesammelten Argumenten
if not "%MAIN_ARGS%"=="" (
    echo Starte System mit Argumenten: %MAIN_ARGS%
    python -m src.main %MAIN_ARGS%
    exit /b %errorlevel%
) else (
    echo Starte System mit Standardargumenten
    python -m src.main --start-rest
    exit /b %errorlevel%
)

REM Behandle das "admin"-Kommando
if "%1"=="admin" (
    shift
    REM Prüfe auf Unterbefehl
    if "%1"=="users" (
        shift
        if "%1"=="create" (
            shift
            REM Setze PYTHONPATH für Admin-Befehle
            set PYTHONPATH=%CD%
            python admin_console\commands\manage_users.py create %*
        ) else if "%1"=="list" (
            shift
            REM Setze PYTHONPATH für Admin-Befehle
            set PYTHONPATH=%CD%
            python admin_console\commands\manage_users.py list %*
        ) else if "%1"=="delete" (
            shift
            REM Setze PYTHONPATH für Admin-Befehle
            set PYTHONPATH=%CD%
            python admin_console\commands\manage_users.py delete %*
        ) else (
            REM Setze PYTHONPATH für Admin-Befehle
            set PYTHONPATH=%CD%
            python admin_console\commands\manage_users.py %*
        )
    ) else (
        echo Unbekannter Admin-Befehl: %1
        exit /b 1
    )
    exit /b %errorlevel%
)

REM Behandle das "help"-Kommando
if "%1"=="help" (
    echo Mindestentinel CLI
    echo -----------------
    echo Verwendung: mindest [command] [options]
    echo.
    echo Befehle:
    echo   start      - Startet das System
    echo   admin      - Verwaltet Benutzer und System
    echo   help       - Zeigt diese Hilfe an
    exit /b 0
)

echo Unbekannter Befehl: %1
exit /b 1