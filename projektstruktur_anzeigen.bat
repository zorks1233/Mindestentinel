@echo off
for /R %%f in (*) do (
    echo %%f | findstr /C:"\.venv\" >nul
    if errorlevel 1 echo %%f
)
pause