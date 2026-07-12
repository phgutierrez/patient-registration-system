@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute setup_windows.bat.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" scripts\verify_setup.py
set "RESULT=%ERRORLEVEL%"
echo.
pause
exit /b %RESULT%
