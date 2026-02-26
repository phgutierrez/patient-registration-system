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
echo   1. Verificar Python 3.11
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
REM VERIFICACAO CRITICA - Python 3.11
REM ===================================================================
echo [VERIFICACAO] Verificando Python 3.11...
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
for /f "tokens=2" %%i in ('python --version 2>&1') do set PYTHON_VERSION=%%i

echo   Python encontrado: %PYTHON_VERSION%

REM Extrair major.minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

REM Verificar se eh Python 3.11+
if "%MAJOR%"=="3" (
    if %MINOR% GEQ 11 (
        echo   [OK] Python 3.%MINOR% atende aos requisitos ^(3.11+ necessario^)
    ) else (
        echo.
        echo [ERRO] Python 3.%MINOR% eh uma versao antiga!
        echo        Este sistema requer Python 3.11 ou posterior.
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
    echo        Este sistema requer Python 3.11 ou posterior.
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
    echo [PRE-SETUP] Criando arquivo .env com configuracoes padrao...
    (
        echo # =================================================================
        echo # Patient Registration System - Configuracao do Ambiente
        echo # Gerado automaticamente pelo setup_windows.bat
        echo # =================================================================
        echo.
        echo SECRET_KEY=patient-reg-secret-key-2026-change-in-production
        echo FLASK_ENV=production
        echo FLASK_DEBUG=0
        echo SERVER_HOST=127.0.0.1
        echo SERVER_PORT=5000
        echo DESKTOP_MODE=false
        echo GOOGLE_CALENDAR_ID=s4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com
        echo GOOGLE_CALENDAR_TZ=America/Fortaleza
        echo CALENDAR_CACHE_TTL_SECONDS=60
        echo CALENDAR_CACHE_TTL_MINUTES=5
        echo GOOGLE_FORMS_EDIT_ID=1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw
        echo GOOGLE_FORMS_PUBLIC_ID=1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg
        echo GOOGLE_FORMS_TIMEOUT=10
        echo APPS_SCRIPT_SCHEDULER_URL=
        echo LIFECYCLE_TIMEOUT_SECONDS=30
        echo LIFECYCLE_HEARTBEAT_SECONDS=5
    ) > .env
    echo   [OK] Arquivo .env criado com sucesso
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
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo.
    echo [AVISO] Houve erro ao instalar algumas dependencias
    echo         Isto pode ser apenas um aviso. Continuando...
    echo.
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

python << PYTHON_SCRIPT
import sys
import os
sys.path.insert(0, os.getcwd())

success = True

try:
    from src.app import create_app
    from src.extensions import db
    from src.models.user import User
    from src.models.specialty import Specialty
    from sqlalchemy import inspect
    
    app = create_app()
    
    with app.app_context():
        print("   - Verificando tabelas do banco de dados...")
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'specialties' not in tables:
            print("   [ERRO] Tabela 'specialties' nao encontrada!")
            print("          Isto significa que as migracoes nao foram aplicadas.")
            print("          Execute manualmente: alembic upgrade head")
            sys.exit(1)
        
        print("   [OK] Tabelas de banco de dados verificadas")
        print()
        
        # Criar especialidades
        print("   - Criando/Verificando especialidades...")
        spec_count = Specialty.query.count()
        
        if spec_count == 0:
            print("     (Nenhuma encontrada, criando...)")
            
            specs = [
                Specialty(slug='ortopedia', name='Ortopedia', is_active=True),
                Specialty(slug='cirurgia_pediatrica', name='Cirurgia Pediatrica', is_active=True),
            ]
            for spec in specs:
                db.session.add(spec)
                print("       + " + spec.name)
            
            db.session.commit()
            print("   [OK] Especialidades criadas com sucesso")
        else:
            print("   [OK] " + str(spec_count) + " especialidade(s) ja existem")
        
        print()
        
        # Criar usuarios
        print("   - Criando/Verificando usuarios...")
        user_count = User.query.count()
        
        if user_count == 0:
            print("     (Nenhum encontrado, criando...)")
            users_data = [
                {'username': 'pedro', 'full_name': 'Pedro Freitas'},
                {'username': 'andre', 'full_name': 'Andre Cristiano'},
                {'username': 'brauner', 'full_name': 'Brauner Cavalcanti'},
                {'username': 'savio', 'full_name': 'Savio Bruno'},
                {'username': 'laecio', 'full_name': 'Laecio Damaceno'},
            ]
            
            for user_data in users_data:
                user = User(
                    username=user_data['username'],
                    password='123456',
                    full_name=user_data['full_name'],
                    specialty_id=1,
                    role='solicitante'
                )
                db.session.add(user)
                print("       + " + user_data['username'] + " (" + user_data['full_name'] + ")")
            
            db.session.commit()
            print("   [OK] Usuarios criados com sucesso")
        else:
            print("   [OK] " + str(user_count) + " usuario(s) ja existe(m)")
        
        print()
        print("   [OK] Dados inicializados com sucesso!")
        print()
        print("===============================================================================")
        print("  RESUMO DA INICIALIZACAO:")
        print("===============================================================================")
        print("  - Especialidades: " + str(Specialty.query.count()))
        print("  - Usuarios: " + str(User.query.count()))
        print()
        
except ImportError as e:
    print("   [ERRO] Falha ao importar modulos do sistema")
    print("          Detalhes: " + str(e))
    success = False
    
except Exception as e:
    print("   [ERRO] Erro nao esperado durante inicializacao")
    print("          Detalhes: " + str(e))
    success = False

if not success:
    sys.exit(1)

PYTHON_SCRIPT

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
echo Credenciais padrao:
echo   - Usuario: pedro ^(ou outros usuarios criados^)
echo   - Senha: 123456
echo.
echo Para mais informacoes, ver: INSTALLATION_GUIDE.md
echo.
pause

endlocal
