@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute setup_windows.bat.
    pause
    exit /b 1
)

echo Modo rede: acesse http://IP-DESTE-COMPUTADOR:5000
ipconfig | findstr /R /C:"IPv4"
echo.
".venv\Scripts\python.exe" server.py --mode network %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
    echo.
    echo [ERRO] O servidor de rede nao iniciou. Consulte logs\patient-registration.log.
    pause
)
exit /b %RESULT%
