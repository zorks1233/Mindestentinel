@echo off
setlocal
cd /d "%~dp0"
.venv\Scripts\activate && mindest.bat start --rest --autonomy --port 8000
