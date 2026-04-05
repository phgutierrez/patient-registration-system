@echo off
REM ===============================================================================
REM SETUP WINDOWS - Patient Registration System
REM Inicializacao completa do sistema para Windows
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================================
echo  SETUP DO SISTEMA - Patient Registration System
echo ===============================================================================
echo.
echo Este script realizara tudo que eh necessario para rodar o sistema:
echo   1. Verificar Python 3.10+
echo   2. Criar ambiente virtual
echo   3. Instalar dependencias
echo   4. Criar banco de dados
echo   5. Aplicar migracoes
echo   6. Inserir dados iniciais
echo.
echo ===============================================================================
echo.

REM ===================================================================
REM VERIFICACAO INICIAL - Diretorio
REM ===================================================================
echo [VERIFICACAO] Verificando diretorio do projeto...
if not exist "requirements.txt" (
    echo.
    echo [ERRO] Arquivo requirements.txt nao encontrado!
    echo        Certifique-se de estar no diretorio raiz do projeto.
    echo.
    pause
    exit /b 1
)
echo   [OK] Arquivo requirements.txt encontrado.
echo.

REM ===================================================================
REM VERIFICACAO CRITICA - Python 3.10+
REM ===================================================================
echo [VERIFICACAO] Verificando Python 3.10+...
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no PATH!
    echo.
    echo Solucoes:
    echo   1. Instale Python 3.11 via winget:
    echo      - Abra PowerShell como administrador
    echo      - Execute: winget install Python.Python.3.11
    echo.
    echo   2. Ou baixe em: https://www.python.org/downloads/
    echo.
    echo   3. Apos instalar, reinicie este script.
    echo.
    pause
    exit /b 1
)

REM Verificar versao exata do Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i

echo   Python encontrado: %PYTHON_VERSION%

REM Extrair major.minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

REM Verificar se eh Python 3.10+
if "%MAJOR%"=="3" (
    if %MINOR% GEQ 10 (
        echo   [OK] Python 3.%MINOR% atende aos requisitos ^(3.10+ necessario^)
    ) else (
        echo.
        echo [ERRO] Python 3.%MINOR% eh uma versao antiga!
        echo        Este sistema requer Python 3.10 ou posterior.
        echo.
        echo Solucoes:
        echo   1. Instale Python 3.11 via winget:
        echo      - Abra PowerShell como administrador
        echo      - Execute: winget install Python.Python.3.11
        echo.
        echo   2. Ou baixe em: https://www.python.org/downloads/
        echo.
        echo Apos instalar, reinicie este script.
        echo.
        pause
        exit /b 1
    )
) else (
    echo.
    echo [ERRO] Python %MAJOR%.%MINOR% nao eh compativel!
    echo        Este sistema requer Python 3.10 ou posterior.
    echo.
    echo Solucoes:
    echo   1. Instale Python 3.11 via winget:
    echo      - Abra PowerShell como administrador
    echo      - Execute: winget install Python.Python.3.11
    echo.
    echo   2. Ou baixe em: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.

REM ===================================================================
REM PRE-SETUP: Criar .env se nao existir
REM ===================================================================
if not exist ".env" (
    echo [PRE-SETUP] Copiando .env.example para .env...
    copy /Y ".env.example" ".env" > nul
    echo   [OK] Arquivo .env criado com sucesso
    echo   [AVISO] Preencha ADMIN_BOOTSTRAP_USERNAME e ADMIN_BOOTSTRAP_PASSWORD antes do primeiro login
) else (
    echo [PRE-SETUP] Arquivo .env ja existe ^(configuracoes preservadas^).
)
echo.

REM ===================================================================
REM PASSO 1: Criar/Verificar Ambiente Virtual
REM ===================================================================
echo [PASSO 1/5] Verificando ambiente virtual...

if not exist ".venv\" (
    echo   - Criando novo ambiente virtual...
    python -m venv .venv
    
    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao criar ambiente virtual!
        echo.
        pause
        exit /b 1
    )
    echo   [OK] Ambiente virtual criado
) else (
    echo   [OK] Ambiente virtual ja existe
)

echo.

REM ===================================================================
REM PASSO 2: Ativar Ambiente Virtual
REM ===================================================================
echo [PASSO 2/5] Ativando ambiente virtual...

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
REM PASSO 3: Instalar Dependencias
REM ===================================================================
echo [PASSO 3/5] Instalando dependencias...

echo   - Atualizando pip...
python -m pip install --upgrade pip --quiet

echo   - Instalando dependencias do requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao instalar dependencias!
    echo        Verifique os erros acima e tente novamente.
    echo.
    pause
    exit /b 1
) else (
    echo   [OK] Dependencias instaladas com sucesso
)

echo.

REM ===================================================================
REM PASSO 4: Criar Banco de Dados
REM ===================================================================
echo [PASSO 4/5] Criando/Atualizando banco de dados...

echo   - Executando create_tables_direct.py...
python create_tables_direct.py

if errorlevel 1 (
    echo   [AVISO] Erro ao executar create_tables_direct.py
    echo           O banco pode ja existir. Continuando...
)

echo   [OK] Banco de dados criado/atualizado

echo.

REM ===================================================================
REM PASSO 5: Inicializar Dados
REM ===================================================================
echo [PASSO 5/5] Inicializando dados do sistema...
echo.

python setup_init_data.py

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao inicializar dados do sistema!
    echo        Voce precisa corrigir isto antes de usar o sistema.
    echo.
    pause
    exit /b 1
)

echo.

REM ===================================================================
REM PASSO FINAL: Registrar estado das migracoes
REM ===================================================================
echo [FINAL] Registrando estado das migracoes...

if exist "migrations\" (
    set FLASK_APP=src/app.py
    flask db stamp head

    if errorlevel 1 (
        echo   [AVISO] Nao foi possivel registrar estado das migracoes.
        echo           Isto pode ser ignorado. O sistema deve funcionar normalmente.
    ) else (
        echo   [OK] Estado das migracoes registrado com sucesso
    )
)

echo.

REM ===================================================================
REM CONCLUSAO
REM ===================================================================
echo ===============================================================================
echo  [OK] SETUP CONCLUIDO COM SUCESSO!
echo ===============================================================================
echo.
echo Proximas acoes:
echo   1. Execute "run_local.bat" para modo desenvolvimento ^(localhost^)
echo   2. Ou execute "run_network.bat" para modo rede ^(LAN^)
echo.
echo Acesso padrao:
echo   - Local: http://localhost:5000
echo   - Rede: http://seu-ip-do-servidor:5000
echo.
echo Bootstrap inicial recomendado:
echo   - Edite o arquivo .env e configure ADMIN_BOOTSTRAP_USERNAME
echo   - Defina ADMIN_BOOTSTRAP_PASSWORD com uma senha forte
echo   - No primeiro login, o sistema exigira troca de senha
echo.
echo Para mais informacoes, ver: INSTALLATION_GUIDE.md
echo.
pause

endlocal
