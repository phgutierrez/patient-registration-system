@echo off
REM ===============================================================================
REM RUN LOCAL - Patient Registration System
REM Executa o sistema no modo LOCAL ^(desenvolvimento/desktop^)
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================================
echo  INICIANDO - Modo LOCAL ^(Desktop^)
echo ===============================================================================
echo.
echo Configuracao:
echo   - Servidor: Waitress ^(performance^)
echo   - Acesso: http://localhost:5000 ^(localhost apenas^)
echo   - Porta: 5000
echo   - Debug: OFF
echo   - Auto-desligamento: ATIVADO
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
    echo   [AVISO] Arquivo .env nao encontrado. Copiando template canonico .env.example...
    copy /Y ".env.example" ".env" > nul
    echo   [OK] Arquivo .env criado a partir de .env.example
    echo   [AVISO] Revise ADMIN_BOOTSTRAP_* e integracoes opcionais antes do primeiro acesso
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

set SERVER_HOST=127.0.0.1
set SERVER_PORT=5000
set DESKTOP_MODE=true
set FLASK_ENV=production
set FLASK_DEBUG=0

echo   [OK] Variaveis configuradas

echo.

REM ===================================================================
REM Mensagem Final e Inicializacao
REM ===================================================================
echo ===============================================================================
echo  SERVIDOR LOCAL INICIANDO
echo ===============================================================================
echo.
echo Acesso:
echo   - Local: http://localhost:5000
echo.
echo Parar o servidor: Feche o navegador
echo ^(O servidor encerrara automaticamente quando voce fechar a janela^)
echo.
echo ===============================================================================
echo.

REM ===================================================================
REM Abrir Navegador Automaticamente
REM ===================================================================
echo [NAVEGADOR] Abrindo http://localhost:%SERVER_PORT% em 2 segundos...
start /b cmd /c "ping -n 3 127.0.0.1 > nul && start http://localhost:%SERVER_PORT%"

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
