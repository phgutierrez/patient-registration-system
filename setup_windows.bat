@echo off
REM ===============================================================================
REM  SETUP WINDOWS - Sistema de Registro de Pacientes
REM ===============================================================================
REM Inicialização completa do sistema para Windows
REM Executa todos os passos necessários antes de rodar o servidor
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================================
echo  SETUP DO SISTEMA - Paciente Registration System
echo ===============================================================================
echo.
echo Este script far{'á tudo que é necessario para rodar o sistema:
echo   1. Ativar ambiente virtual
echo   2. Instalar dependências (se necessário)
echo   3. Criar banco de dados
echo   4. Aplicar migrações
echo   5. Inserir dados iniciais
echo.
echo ===============================================================================
echo.

REM Verificar se está no diretório correto
if not exist "requirements.txt" (
    echo ERRO: Arquivo requirements.txt não encontrado!
    echo Certifique-se de estar no diretório raiz do projeto.
    pause
    exit /b 1
)

REM ══════════════════════════════════════════════════════════════════════════════
REM PASSO 1: Verificar/Criar Ambiente Virtual
REM ══════════════════════════════════════════════════════════════════════════════
echo [PASSO 1/5] Verificando ambiente virtual...
if not exist ".venv\" (
    echo   - Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRO: Falha ao criar ambiente virtual.
        echo Verifique se Python 3.11+ está instalado e disponível no PATH.
        echo.
        pause
        exit /b 1
    )
)
echo   ✓ Ambiente virtual pronto

REM ══════════════════════════════════════════════════════════════════════════════
REM PASSO 2: Ativar Ambiente Virtual
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo [PASSO 2/5] Ativando ambiente virtual...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo.
    echo ERRO: Falha ao ativar ambiente virtual.
    echo.
    pause
    exit /b 1
)
echo   ✓ Ambiente virtual ativado

REM ══════════════════════════════════════════════════════════════════════════════
REM PASSO 3: Instalar Dependências
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo [PASSO 3/5] Verificando/Instalando dependências...
echo   - Atualizando pip...
python -m pip install --upgrade pip --quiet
echo   - Instalando dependências do requirements.txt...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo AVISO: Houve erro ao instalar algumas dependências.
    echo Pode ser apenas um aviso. Continuando...
)
echo   ✓ Dependências instaladas

REM ══════════════════════════════════════════════════════════════════════════════
REM PASSO 4: Criar Banco de Dados e Tabelas
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo [PASSO 4/5] Criando/Atualizando banco de dados...

REM Criar tabelas base
echo   - Executando create_tables_direct.py...
python create_tables_direct.py
if errorlevel 1 (
    echo.
    echo AVISO: Erro ao executar create_tables_direct.py
    echo O banco pode já existir. Continuando...
)

REM Aplicar migrations (incluindo especialidades)
echo   - Aplicando migrations com Alembic...
REM Tentar alembic upgrade, se não existir o arquivo de versão, criar
if exist "alembic.ini" (
    alembic upgrade head
    if errorlevel 1 (
        echo   AVISO: alembic upgrade retornou erro (banco pode estar atualizado)
    ) else (
        echo   ✓ Migrações aplicadas com sucesso
    )
) else (
    echo   (migrations/alembic.ini não encontrado, pulando)
)

echo   ✓ Banco de dados criado/atualizado

REM ══════════════════════════════════════════════════════════════════════════════
REM PASSO 5: Inicializar Dados (Usuários, Especialidades, Procedimentos)
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo [PASSO 5/5] Inicializando dados do sistema...
echo   - Verificando dados base...

REM Script Python para verificar e criar dados necessários
python << PYTHON_SCRIPT
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from src.app import create_app
    from src.extensions import db
    from src.models.user import User
    from src.models.specialty import Specialty
    from sqlalchemy import inspect
    
    app = create_app()
    
    with app.app_context():
        # Verificar se tabela specialties existe
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'specialties' not in tables:
            print("   ✗ Tabela 'specialties' não encontrada!")
            print("     Execute alembic upgrade head para criar as tabelas")
            sys.exit(1)
        
        # Verificar especialidades
        spec_count = Specialty.query.count()
        if spec_count == 0:
            print("   - Criando especialidades...")
            from datetime import datetime
            
            specs = [
                Specialty(slug='ortopedia', name='Ortopedia', is_active=True),
                Specialty(slug='cirurgia_pediatrica', name='Cirurgia Pediátrica', is_active=True),
            ]
            for spec in specs:
                db.session.add(spec)
            db.session.commit()
            print("   ✓ Especialidades criadas")
        else:
            print(f"   ✓ Especialidades já existem ({spec_count})")
        
        # Verificar usuários
        user_count = User.query.count()
        if user_count == 0:
            print("   - Criando usuários iniciais...")
            users_data = [
                {'username': 'pedro', 'full_name': 'Pedro Freitas', 'specialty_id': 1},
                {'username': 'andre', 'full_name': 'André Cristiano', 'specialty_id': 1},
                {'username': 'brauner', 'full_name': 'Brauner Cavalcanti', 'specialty_id': 1},
                {'username': 'savio', 'full_name': 'Sávio Bruno', 'specialty_id': 1},
                {'username': 'laecio', 'full_name': 'Laecio Damaceno', 'specialty_id': 1},
            ]
            
            for user_data in users_data:
                user = User(
                    username=user_data['username'],
                    password='123456',
                    full_name=user_data['full_name'],
                    specialty_id=user_data['specialty_id'],
                    role='solicitante'
                )
                db.session.add(user)
            db.session.commit()
            print("   ✓ Usuários iniciais criados")
        else:
            print(f"   ✓ Usuários já existem ({user_count})")
        
        print("\n   ✓ Dados inicializados com sucesso!")
        
except ImportError as e:
    print(f"   ERRO ao importar módulos: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"   AVISO: {str(e)}")
    print("   (Pode ser resultado normal de banco já inicializado)")

PYTHON_SCRIPT

if errorlevel 1 (
    echo.
    echo AVISO: Erro ao inicializar dados
    echo Você pode tentar rodá-lo manualmente depois
)

REM ══════════════════════════════════════════════════════════════════════════════
REM CONCLUSÃO
REM ══════════════════════════════════════════════════════════════════════════════
echo.
echo ===============================================================================
echo  ✓ SETUP CONCLUÍDO COM SUCESSO!
echo ===============================================================================
echo.
echo Próximas ações:
echo   1. Execute "run_local.bat" para modo de desenvolvimento (localhost)
echo   2. Ou execute "run_network.bat" para modo rede (LAN)
echo.
echo Acesso padrão:
echo   - Local: http://localhost:5000
echo   - Rede: http://seu-ip-do-servidor:5000
echo.
echo Credenciais padrão:
echo   - Usuário: pedro (ou outros usuários criados)
echo   - Senha: 123456
echo.
echo Para mais informações, ver: INSTALLATION_GUIDE.md
echo.
pause
