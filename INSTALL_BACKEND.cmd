@echo off
setlocal
cd /d "%~dp0"
echo Activity Lab - CPU backend installer and launcher
echo Downloads uv / Python 3.12 if missing, CPU dependencies, and pretrained models.
echo First setup requires Internet. Existing .env is preserved.
where uv >nul 2>nul
if errorlevel 1 goto bootstrap
set "ACTIVITY_UV=uv"
goto install
:bootstrap
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "ACTIVITY_UV=%USERPROFILE%\.local\bin\uv.exe"
    goto install
)
echo Installing uv from its official source: https://astral.sh/uv/install.ps1
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression"
if errorlevel 1 goto failed
set "ACTIVITY_UV=%USERPROFILE%\.local\bin\uv.exe"
if not exist "%ACTIVITY_UV%" goto failed
:install
call "%ACTIVITY_UV%" run --no-project --python 3.12 python scripts/install_backend.py --uv "%ACTIVITY_UV%" %*
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Installation or backend failed. Read the error above. Existing files were not deleted.
pause
exit /b 1
