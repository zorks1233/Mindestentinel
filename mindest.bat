@echo off
REM Mindestentinel CLI Starter - Einfache und zuverlässige Version

REM Prüfe, ob .venv existiert
if not exist ".venv" (
    echo Fehler: Virtuelle Umgebung nicht gefunden. Bitte fuehren Sie zuerst install.bat aus.
    exit /b 1
)

REM Aktiviere virtuelle Umgebung
call .venv\Scripts\activate.bat

REM Setze PYTHONPATH
set PYTHONPATH=%CD%

REM Prüfe, ob der erste Parameter "start" ist
if "%1"=="start" (
    shift
    set MAIN_ARGS=
    
    :arg_loop
    if "%1"=="" goto start_system
    
    if "%1"=="--rest" (
        set MAIN_ARGS=%MAIN_ARGS% --start-rest
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
    ) else if "%1"=="--debug" (
        set MAIN_ARGS=%MAIN_ARGS% --debug
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
)

REM Prüfe, ob der erste Parameter "admin" ist
if "%1"=="admin" (
    if "%2"=="users" (
        if "%3"=="update-password" (
            shift
            shift
            shift
            set PYTHONPATH=%CD%
            python admin_console\commands\manage_users.py update-password --username %1 --password %2
            exit /b %errorlevel%
        )
    )
)

REM Standard: Leite alle Befehle direkt an das Hauptprogramm weiter
python -m src.main %*