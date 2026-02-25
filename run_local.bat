@echo off
REM ===============================================================================
REM  RUN LOCAL - Sistema de Registro de Pacientes
REM ===============================================================================
REM Executa o sistema no modo LOCAL (desenvolvimento/desktop)
REM - Servidor WSGI Waitress (melhor performance que Flask dev server)
REM - Localhost apenas (sem acesso LAN)
REM - Auto-desligamento ao fechar navegador (desktop mode)
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================================
echo  INICIANDO - Modo LOCAL (Desktop)
echo ===============================================================================
echo.
echo Configuração:
echo   - Servidor: Waitress
echo   - Acesso: http://localhost:5000 (localhost apenas)
echo   - Porta: 5000
echo   - Debug: OFF (máxima performance)
echo   - Auto-desligamento: ATIVADO
echo.

REM Verificar se arquivo setup foi rodado
if not exist "instance\prontuario.db" (
    echo AVISO: Banco de dados não encontrado!
    echo.
    echo Execute primeiro: setup_windows.bat
    echo.
    pause
    exit /b 1
)

REM Verificar ambiente virtual
if not exist ".venv\Scripts\activate.bat" (
    echo ERRO: Ambiente virtual não encontrado!
    echo Execute: setup_windows.bat
    pause
    exit /b 1
)

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao ativar ambiente virtual
    pause
    exit /b 1
)

REM Definir variáveis de ambiente
set SERVER_HOST=127.0.0.1
set SERVER_PORT=5000
set DESKTOP_MODE=true
set FLASK_ENV=production
set FLASK_DEBUG=0

REM Espaço visual
echo.
echo Iniciando servidor...
echo   Acesso: http://localhost:5000
echo   Feche o navegador para encerrar
echo.
echo ===============================================================================
echo.

REM Iniciar servidor Waitress
waitress-serve --listen=%SERVER_HOST%:%SERVER_PORT% wsgi:application

REM Se chegou aqui, servidor foi encerrado
echo.
echo ===============================================================================
echo  Servidor encerrado.
echo ===============================================================================
pause