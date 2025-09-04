@echo off
REM setup_and_run.bat - Windows CMD friendly setup script for Mindestentinel project
REM Usage:
REM   - Open Command Prompt (cmd.exe) as normal user
REM   - cd to project root (where this file is located)
REM   - run: setup_and_run.bat [install] [applypatches] [test] [start] [detach] [port 8000]
REM Example:
REM   setup_and_run.bat install test start port 8000

SETLOCAL ENABLEDELAYEDEXPANSION

REM ---- Config / defaults ----
SET ROOT_DIR=%~dp0..
PUSHD %ROOT_DIR%
SET VENV_DIR=%ROOT_DIR%\.venv
SET REQ_FILE=%ROOT_DIR%\requirements.txt
SET ENV_FILE=%ROOT_DIR%\.env
SET PORT=8000
SET INSTALL_REQS=false
SET APPLY_PATCHES=false
SET RUN_TESTS=false
SET DO_START=false
SET DETACH=false

REM ---- Parse args ----
:parse_args
IF "%~1"=="" GOTO args_done
IF /I "%~1"=="install" (SET INSTALL_REQS=true) ELSE (
IF /I "%~1"=="applypatches" (SET APPLY_PATCHES=true) ELSE (
IF /I "%~1"=="test" (SET RUN_TESTS=true) ELSE (
IF /I "%~1"=="start" (SET DO_START=true) ELSE (
IF /I "%~1"=="detach" (SET DETACH=true) ELSE (
IF /I "%~1"=="port" (
  SHIFT
  IF "%~1"=="" (
    ECHO Missing port value after 'port'
    GOTO usage
  )
  SET PORT=%~1
) ELSE (
  ECHO Unknown argument: %~1
)
)))))

SHIFT
GOTO parse_args
:args_done

ECHO Working directory: %CD%

REM ---- Find python binary ----
SET PYTHON_CMD=
FOR %%p IN (python3.13.exe python3.exe python.exe) DO (
  WHERE %%p >NUL 2>&1
  IF NOT ERRORLEVEL 1 (
    SET PYTHON_CMD=%%p
    GOTO found_python
  )
)
:found_python
IF "%PYTHON_CMD%"=="" (
  ECHO Python executable not found in PATH. Please install Python 3.12+ and add to PATH.
  GOTO end
)
ECHO Using python: %PYTHON_CMD%
%PYTHON_CMD% --version

REM ---- Create venv if missing ----
IF NOT EXIST "%VENV_DIR%" (
  ECHO Creating virtualenv in %VENV_DIR% ...
  %PYTHON_CMD% -m venv "%VENV_DIR%"
) ELSE (
  ECHO Virtualenv exists: %VENV_DIR%
)

REM Activate venv for this script
CALL "%VENV_DIR%\Scripts\activate.bat"

REM ---- Install requirements if requested ----
IF /I "%INSTALL_REQS%"=="true" (
  IF EXIST "%REQ_FILE%" (
    ECHO Installing requirements from %REQ_FILE% ...
    python -m pip install --upgrade pip setuptools wheel
    python -m pip install -r "%REQ_FILE%"
  ) ELSE (
    ECHO requirements.txt not found. Installing minimal runtime packages...
    python -m pip install --upgrade pip setuptools wheel
    python -m pip install fastapi "uvicorn[standard]" python-multipart pyyaml numpy requests
  )
)

REM ---- Create .env with MIND_API_KEY if not exists ----
IF NOT EXIST "%ENV_FILE%" (
  ECHO Generating a new MIND_API_KEY and writing to %ENV_FILE% ...
  FOR /F "usebackq delims=" %%K IN (`%PYTHON_CMD% -c "import secrets; print(secrets.token_urlsafe(48))"`) DO SET NEW_KEY=%%K
  ECHO # Auto-generated .env> "%ENV_FILE%"
  ECHO MIND_API_KEY=%NEW_KEY%>> "%ENV_FILE%"
  ECHO .env created (DO NOT commit .env to version control).
) ELSE (
  ECHO .env exists. Using existing environment settings.
)

REM ---- Load .env into session (simple parser) ----
REM Use python helper to print key=value pairs then import into session
FOR /F "usebackq delims=" %%E IN (`%PYTHON_CMD% - <<PY
import os,sys
p = os.path.join(r"%ROOT_DIR%", ".env")
if os.path.exists(p):
    for l in open(p):
        l=l.strip()
        if not l or l.startswith('#'): continue
        if '=' in l:
            k,v = l.split('=',1)
            print(k + "::: " + v)
PY`) DO (
  FOR /F "tokens=1* delims=:::" %%K IN ("%%E") DO (
    SET "ENVKEY=%%K"
    SET "ENVVAL=%%L"
    REM Set for current session
    SET !ENVKEY!=!ENVVAL!
    REM Also persist in user environment for future logins (setx)
    SETX !ENVKEY! "!ENVVAL!" >NUL
  )
)

IF NOT DEFINED MIND_API_KEY (
  ECHO ERROR: MIND_API_KEY not set. Aborting.
  GOTO end
)

REM ---- Apply patches (if requested) ----
IF /I "%APPLY_PATCHES%"=="true" (
  IF EXIST "%ROOT_DIR%\patches" (
    FOR %%f IN ("%ROOT_DIR%\patches\*.patch") DO (
      ECHO Applying patch %%f ...
      git apply "%%f" 2>NUL || patch -p0 < "%%f"
      IF ERRORLEVEL 1 (
        ECHO Failed to apply patch %%f
        REM continue but warn
      ) ELSE (
        ECHO Patch applied: %%f
      )
    )
  ) ELSE (
    ECHO No patches directory present, skipping.
  )
)

REM ---- Syntax check ----
ECHO Running syntax check (compileall) ...
%PYTHON_CMD% -m compileall -q .

REM ---- Run tests if requested ----
IF /I "%RUN_TESTS%"=="true" (
  ECHO Running unit tests ...
  %PYTHON_CMD% -m unittest discover -s tests -v
)

REM ---- Start server if requested ----
IF /I "%DO_START%"=="true" (
  IF /I "%DETACH%"=="true" (
    ECHO Starting server detached (background) ...
    START "Mindestentinel" cmd /c "%PYTHON_CMD% src\main.py --start-rest --api-port %PORT% > logs\server.out 2>&1"
    ECHO Server started in background. Logs: logs\server.out
  ) ELSE (
    ECHO Starting server in foreground on port %PORT% ...
    %PYTHON_CMD% src\main.py --start-rest --api-port %PORT%
  )
) ELSE (
  ECHO Setup complete. To start server: CALL "%VENV_DIR%\Scripts\activate.bat" && python src\main.py --start-rest --api-port %PORT%
)

:end
POPD
ENDLOCAL
