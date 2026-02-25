@echo off
REM ===============================================================================
REM RUN NETWORK - Patient Registration System
REM Executa o sistema no modo REDE (LAN hospitalar/multi-usuario)
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================================
echo  INICIANDO - Modo REDE ^(LAN/Multi-usuario^)
echo ===============================================================================
echo.
echo Configuracao:
echo   - Servidor: Waitress ^(performance^)
echo   - Acesso: Rede LAN ^(0.0.0.0:5000^)
echo   - Porta: 5000
echo   - Debug: OFF
echo   - Auto-desligamento: DESATIVADO
echo.
echo ===============================================================================
echo.

REM ===================================================================
REM Verificacao 1: Banco de dados
REM ===================================================================
echo [VERIFICACAO] Procurando banco de dados...

if not exist "instance\prontuario.db" (
    echo.
    echo [ERRO] Banco de dados nao encontrado!
    echo        Arquivo esperado: instance\prontuario.db
    echo.
    echo Solucao:
    echo   Execute primeiramente: setup_windows.bat
    echo.
    pause
    exit /b 1
)

echo   [OK] Banco de dados encontrado

REM ===================================================================
REM Verificacao 2: Arquivo de configuracao .env
REM ===================================================================
echo [VERIFICACAO] Procurando arquivo .env...

if not exist ".env" (
    echo.
    echo [ERRO] Arquivo .env nao encontrado!
    echo.
    echo Solucao:
    echo   1. Copie .env.example para .env
    echo   2. Configure as variaveis conforme INSTALLATION_GUIDE.md
    echo.
    pause
    exit /b 1
)

echo   [OK] Arquivo .env encontrado

REM ===================================================================
REM Verificacao 3: Ambiente virtual
REM ===================================================================
echo [VERIFICACAO] Procurando ambiente virtual...

if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [ERRO] Ambiente virtual nao encontrado!
    echo        Diretorio esperado: .venv\
    echo.
    echo Solucao:
    echo   Execute: setup_windows.bat
    echo.
    pause
    exit /b 1
)

echo   [OK] Ambiente virtual encontrado

echo.

REM ===================================================================
REM Ativar Ambiente Virtual
REM ===================================================================
echo [CONFIGURACAO] Ativando ambiente virtual...

call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao ativar ambiente virtual!
    echo.
    pause
    exit /b 1
)

echo   [OK] Ambiente virtual ativado

echo.

REM ===================================================================
REM Configurar Variaveis de Ambiente
REM ===================================================================
echo [CONFIGURACAO] Definindo variaveis de ambiente...

set SERVER_HOST=0.0.0.0
set SERVER_PORT=5000
set DESKTOP_MODE=false
set FLASK_ENV=production
set FLASK_DEBUG=0

echo   [OK] Variaveis configuradas

echo.

REM ===================================================================
REM Obter IP Local
REM ===================================================================
echo [CONFIGURACAO] Detectando endereco IP local...

for /f "tokens=2 delims=: " %%A in ('ipconfig ^| findstr /R "IPv4"') do (
    set "IP=%%A"
    goto :got_ip
)

:got_ip

if "%IP%"=="" (
    set "IP=consulte ipconfig"
)

echo   [OK] Endereco IP local detectado

echo.

REM ===================================================================
REM Mensagem Final e Inicializacao
REM ===================================================================
echo ===============================================================================
echo  SERVIDOR DE REDE INICIANDO
echo ===============================================================================
echo.
echo Acesso:
echo   - Local (este computador):  http://localhost:5000
echo   - Rede ^(outros computadores^): http://%IP%:5000
echo.
echo Parar o servidor: Pressione CTRL+C
echo.
echo ===============================================================================
echo.

REM ===================================================================
REM Iniciar Servidor Waitress
REM ===================================================================
waitress-serve --listen=%SERVER_HOST%:%SERVER_PORT% wsgi:application

REM Se chegou aqui, servidor foi encerrado
echo.
echo ===============================================================================
echo  Servidor encerrado
echo ===============================================================================
echo.
pause

endlocal
