@echo off
setlocal

set "APP_DIR=%~dp0"

echo Starting Hamster Storage Manager...
echo Starting backend service...
start "" /min cmd /k python "%APP_DIR%backend\back.py"

timeout /t 3 /nobreak >nul

echo Opening frontend...
start "" "%APP_DIR%MainUI.html"

echo Startup complete.
endlocal
