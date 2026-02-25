@echo off
setlocal

REM Local mode - Run Flask app for single-user desktop use
REM Auto-shutdown when browser is closed (desktop mode)

echo Starting Patient Registration System in LOCAL mode...
echo.
echo Configuration:
echo - Server: Waitress (production WSGI server)
echo - Host: 127.0.0.1 (localhost only)
echo - Port: 5000
echo - Debug: OFF
echo - Auto-shutdown: ENABLED (closes when browser exits)
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERRO] Nao foi possivel ativar o ambiente virtual (.venv).
    pause
    exit /b 1
)

REM Set local mode configuration
set SERVER_HOST=127.0.0.1
set SERVER_PORT=5000
set DESKTOP_MODE=true
set FLASK_ENV=production
set FLASK_DEBUG=0

echo Starting server...
echo Access: http://localhost:5000
echo.

REM Start Waitress in a new window/process
start "Patient Registration System - Server" cmd /c waitress-serve --listen=%SERVER_HOST%:%SERVER_PORT% wsgi:application

REM Wait until server responds before opening browser
set /a MAX_TRIES=30
set /a TRY=0

echo Waiting for server to become available...

:WAIT_LOOP
set /a TRY+=1

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5000' -TimeoutSec 2; exit 0 } catch { exit 1 }"

if %ERRORLEVEL%==0 goto SERVER_READY

if %TRY% GEQ %MAX_TRIES% goto SERVER_TIMEOUT

echo   Attempt %TRY%/%MAX_TRIES% - server not ready yet...
timeout /t 1 /nobreak >nul
goto WAIT_LOOP

:SERVER_READY
echo Server is ready. Opening browser...
start "" http://localhost:5000
echo Done.
exit /b 0

:SERVER_TIMEOUT
echo [ERRO] O servidor nao respondeu apos %MAX_TRIES% segundos.
echo Verifique se houve erro ao iniciar o Waitress (janela do servidor).
pause
exit /b 1