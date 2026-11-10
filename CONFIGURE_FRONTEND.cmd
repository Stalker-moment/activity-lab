@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-backend-cpu\Scripts\python.exe" (
    echo Run INSTALL_BACKEND.cmd first.
    pause
    exit /b 1
)
".venv-backend-cpu\Scripts\python.exe" scripts\configure_frontend.py %*
if errorlevel 1 (
    pause
    exit /b 1
)
echo Restart START_BACKEND.cmd after stopping the old backend with Ctrl+C.
pause
