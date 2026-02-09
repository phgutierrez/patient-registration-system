@echo off
REM Network mode - Run Flask app on LAN using Waitress (production server)
REM Access from other computers: http://192.168.0.X:5000

echo Starting Patient Registration System in NETWORK mode...
echo.
echo Configuration:
echo - Server: Waitress (production WSGI server)
echo - Host: 0.0.0.0 (LAN accessible)
echo - Port: 5000
echo - Debug: OFF
echo - Auto-shutdown: DISABLED (safe for multi-user)
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set network mode configuration
set SERVER_HOST=0.0.0.0
set SERVER_PORT=5000
set DESKTOP_MODE=false
set FLASK_ENV=production
set FLASK_DEBUG=0

REM Start the application with Waitress
echo Starting server... Press Ctrl+C to stop.
echo Access from this computer: http://localhost:5000
echo Access from network: http://YOUR_IP_ADDRESS:5000
echo.
waitress-serve --listen=%SERVER_HOST%:%SERVER_PORT% wsgi:application