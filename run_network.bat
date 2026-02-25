@echo off
REM ===============================================================================
REM  RUN NETWORK - Sistema de Registro de Pacientes
REM ===============================================================================
REM Executa o sistema no modo REDE (LAN hospitalar/multi-usuário)
REM - Servidor WSGI Waitress (melhor performance que Flask dev server)
REM - Acessível de outros computadores na rede
REM - Sem auto-desligamento (seguro para ambiente hospitalar)
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================================
echo  INICIANDO - Modo REDE (LAN/Multi-usuário)
echo ===============================================================================
echo.
echo Configuração:
echo   - Servidor: Waitress
echo   - Acesso: Rede LAN (0.0.0.0:5000)
echo   - Porta: 5000
echo   - Debug: OFF (máxima performance)
echo   - Auto-desligamento: DESATIVADO
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
set SERVER_HOST=0.0.0.0
set SERVER_PORT=5000
set DESKTOP_MODE=false
set FLASK_ENV=production
set FLASK_DEBUG=0

REM Obter IP local
for /f "tokens=2 delims=: " %%A in ('ipconfig ^| findstr /R "IPv4"') do (
    set "IP=%%A"
    goto :got_ip
)
:got_ip

REM Espaço visual
echo.
echo Iniciando servidor de rede...
echo   Local: http://localhost:5000
echo   Rede:  http://%IP%:5000
echo.
echo Pressione CTRL+C para encerrar
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