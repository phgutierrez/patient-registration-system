@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute setup_windows.bat.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" server.py --mode local %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    echo.
    echo [ERRO] O sistema nao iniciou. Consulte logs\patient-registration.log.
    pause
)
exit /b %RESULT%
