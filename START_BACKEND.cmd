@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-backend-cpu\Scripts\python.exe" (
    echo Run INSTALL_BACKEND.cmd first.
    pause
    exit /b 1
)
".venv-backend-cpu\Scripts\python.exe" scripts\install_backend.py --start-only
if errorlevel 1 pause
