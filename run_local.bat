@echo off
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

REM Set local mode configuration
set SERVER_HOST=127.0.0.1
set SERVER_PORT=5000
set DESKTOP_MODE=true
set FLASK_ENV=production
set FLASK_DEBUG=0

REM Start the application with Waitress
echo Starting server... Close browser to stop.
echo Access: http://localhost:5000
echo.
waitress-serve --listen=%SERVER_HOST%:%SERVER_PORT% wsgi:application