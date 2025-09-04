\
    @echo off
    REM create_venv_and_zip.bat
    REM Usage: create_venv_and_zip.bat C:\path\to\project [withreqs]
    SET PROJ_DIR=%1
    IF "%PROJ_DIR%"=="" SET PROJ_DIR=.
    SET WITHREQS=%2
    PUSHD %PROJ_DIR%
    SET PY=python3.13
    WHERE %PY% >NUL 2>&1 || (FOR %%p IN (python3.exe python.exe) DO WHERE %%p >NUL 2>&1 && SET PY=%%p)
    %PY% -m venv .venv
    CALL .venv\Scripts\activate.bat
    python -m pip install --upgrade pip setuptools wheel
    IF /I "%WITHREQS%"=="withreqs" (
      IF EXIST requirements.txt (
        pip install -r requirements.txt
      )
    )
    REM create zip in parent folder
    powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory((Get-Location).Path, (Join-Path (Get-Location).Parent.FullName -ChildPath ((Split-Path -Leaf (Get-Location)) + '-with-venv.zip')) )"
    POPD
    ECHO Done.
