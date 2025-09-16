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

REM Prüfe auf Befehle
if "%1"=="" goto help
if "%1"=="help" goto help

REM Behandle das "start"-Kommando
if "%1"=="start" goto start_command

REM Behandle das "admin"-Kommando
if "%1"=="admin" goto admin_command

REM Behandle das "create-release"-Kommando
if "%1"=="create-release" goto create_release

REM Unbekannter Befehl
echo Unbekannter Befehl: %1
goto help

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
) else if "%1"=="--debug" (
    set MAIN_ARGS=%MAIN_ARGS% --debug
) else (
    echo Unbekanntes Argument: %1
    goto help
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

:create_release
echo Erstelle Release-Paket...
echo.
echo Entferne temporäre Dateien...
del /q /f release.zip 2>nul
rmdir /s /q release 2>nul

echo Erstelle Release-Verzeichnis...
mkdir release
xcopy /s /i /y /exclude:release_exclude.txt * release\

echo Packe Release...
cd release
powershell Compress-Archive -Path * -DestinationPath ..\Mindestentinel_release.zip -Force
cd ..

echo Cleanup...
rmdir /s /q release

echo Release erstellt: Mindestentinel_release.zip
echo.
echo Hinweis: Dieses Release enthält keine virtuelle Umgebung (.venv).
echo        Installieren Sie Abhängigkeiten mit 'pip install -r requirements.txt'
exit /b 0

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
)

if "%1"=="list" (
    shift
    set PYTHONPATH=%CD%
    python admin_console\commands\manage_users.py list %*
    exit /b %errorlevel%
)

if "%1"=="delete" (
    shift
    set PYTHONPATH=%CD%
    python admin_console\commands\manage_users.py delete %*
    exit /b %errorlevel%
)

if "%1"=="update-password" (
    shift
    set USERNAME=
    set PASSWORD=
    
    :parse_args
    if "%1"=="" goto run_update_password
    
    if "%1"=="--username" (
        set USERNAME=%2
        shift
        shift
        goto parse_args
    )
    
    if "%1"=="--password" (
        set PASSWORD=%2
        shift
        shift
        goto parse_args
    )
    
    echo Unbekanntes Argument: %1
    exit /b 1
    
    :run_update_password
    if "%USERNAME%"=="" (
        echo Fehler: --username ist erforderlich
        exit /b 1
    )
    
    if "%PASSWORD%"=="" (
        echo Fehler: --password ist erforderlich
        exit /b 1
    )
    
    set PYTHONPATH=%CD%
    python admin_console\commands\manage_users.py update-password --username "%USERNAME%" --password "%PASSWORD%"
    exit /b %errorlevel%
)

echo Unbekannter Benutzer-Befehl: %1
exit /b 1

:help
echo Mindestentinel CLI
echo -----------------
echo Verwendung: mindest [command] [options]
echo.
echo Befehle:
echo   start      - Startet das System
echo   admin      - Verwaltet Benutzer und System
echo   create-release - Erstellt ein Release-Paket
echo   help       - Zeigt diese Hilfe an
echo.
echo Benutzer-Verwaltung:
echo   mindest admin users create --username ^<name^> --password "pass" [--admin]
echo   mindest admin users list
echo   mindest admin users delete --username ^<name^>
echo   mindest admin users update-password --username ^<name^> --password "new_pass"
echo.
echo Beispiele:
echo   mindest start --rest --autonomy --port 8000
echo   mindest admin users update-password --username admin --password "Bibimax1984@!"
echo   mindest create-release
exit /b 0