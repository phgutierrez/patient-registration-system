@echo off
REM ===============================================================================
REM VERIFY SETUP - Patient Registration System
REM Verifica se o setup foi feito corretamente
REM ===============================================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================================================
echo  VERIFICACAO DO SETUP
echo ===============================================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo        Execute setup_windows.bat primeiro.
    echo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo [VERIFICANDO] Estado do banco de dados...
echo.

python << PYTHON_SCRIPT
import sys
import os
sys.path.insert(0, os.getcwd())

from src.app import create_app
from src.extensions import db
from src.models.user import User
from src.models.specialty import Specialty
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print("=== TABELAS DO BANCO DE DADOS ===")
    print(f"Total de tabelas: {len(tables)}")
    print()
    
    if 'specialties' not in tables:
        print("[ERRO] Tabela 'specialties' nao encontrada!")
        sys.exit(1)
    
    if 'users' not in tables:
        print("[ERRO] Tabela 'users' nao encontrada!")
        sys.exit(1)
    
    print("[OK] Tabelas obrigatorias existem")
    print()
    
    print("=== ESPECIALIDADES ===")
    specs = Specialty.query.order_by(Specialty.name).all()
    
    if len(specs) == 0:
        print("[ERRO] NENHUMA ESPECIALIDADE ENCONTRADA!")
        print()
        print("Isto eh o problema! As especialidades precisam existir para que")
        print("o sistema funcione. Tente:")
        print()
        print("1. Deletar o banco: del instance\prontuario.db")
        print("2. Rodar novamente: setup_windows.bat")
        print()
        sys.exit(1)
    
    for spec in specs:
        status = "[ATIVADA]" if spec.is_active else "[INATIVA]"
        print(f"  - {spec.name} ({spec.id}) {status}")
    
    print()
    print(f"Total: {len(specs)} especialidade(s)")
    print()
    
    print("=== USUARIOS ===")
    users = User.query.order_by(User.full_name).all()
    
    if len(users) == 0:
        print("[AVISO] Nenhum usuario encontrado!")
        print("        Voce pode usar o sistema mas sem dados iniciais.")
    else:
        for user in users:
            spec_name = user.specialty.name if user.specialty else "Sem especialidade"
            print(f"  - {user.full_name} ({user.username}) -> {spec_name}")
        
        print()
        print(f"Total: {len(users)} usuario(s)")
    
    print()
    print("=== RESULTADO ===")
    
    if len(specs) > 0:
        print("[OK] SETUP COMPLETADO COM SUCESSO!")
        print()
        print("Voce pode executar:")
        print("  - run_local.bat   (para modo desktop)")
        print("  - run_network.bat (para modo rede/LAN)")
    else:
        print("[ERRO] Setup incompleto - faltam especialidades")
        sys.exit(1)

PYTHON_SCRIPT

if errorlevel 1 (
    echo.
    echo [ERRO] Verificacao falhou!
    echo        Voce precisa corrigir isto antes de usar o sistema.
)

echo.
pause

endlocal
