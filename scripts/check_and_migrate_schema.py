"""
Schema Check and Auto-Migration Script

Verifica se o banco de dados SQLite tem todas as colunas necessárias
e executa a migration automaticamente se necessário.

USO:
    python scripts/check_and_migrate_schema.py
    
VARIÁVEIS DE AMBIENTE:
    AUTO_MIGRATE=true  - Executa alembic upgrade head se schema estiver desatualizado
    VERBOSE=true       - Exibe informações detalhadas
"""

import sys
import os
import subprocess
from pathlib import Path
import sqlite3
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app import create_app
from src.extensions import db


class SchemaChecker:
    """Verifica se o schema do SQLite está atualizado."""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.app = create_app()
    
    def log(self, message, level='INFO'):
        """Log formatado."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        icon = {
            'INFO': 'ℹ️ ',
            'OK': '✅',
            'WARNING': '⚠️ ',
            'ERROR': '❌',
            'CHECK': '🔍'
        }.get(level, '•')
        
        if self.verbose or level in ['ERROR', 'WARNING']:
            print(f"{icon} [{timestamp}] {message}")
    
    def get_db_path(self):
        """Obtém caminho do banco de dados."""
        with self.app.app_context():
            db_uri = self.app.config['SQLALCHEMY_DATABASE_URI']
            # sqlite:////path/to/db -> /path/to/db
            db_path = db_uri.replace('sqlite:///', '').replace('sqlite:///', '')
            return db_path
    
    def check_column_exists(self, table_name, column_name):
        """Verifica se uma coluna existe na tabela."""
        db_path = self.get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # PRAGMA table_info retorna info de cada coluna
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            conn.close()
            
            column_names = [col[1] for col in columns]  # col[1] é o nome
            
            return column_name in column_names
            
        except Exception as e:
            self.log(f"Erro ao verificar coluna {table_name}.{column_name}: {e}", 'ERROR')
            return False
    
    def check_surgery_request_columns(self):
        """Verifica se as colunas de agendamento existem em surgery_requests."""
        required_columns = {
            'scheduled_at': 'DateTime para timestamp de agendamento',
            'scheduled_event_id': 'String com ID do evento Google Calendar',
            'scheduled_event_link': 'String com link do evento',
            'calendar_status': 'String com status (agendado, erro, etc.)'
        }
        
        self.log("Verificando colunas de agendamento em surgery_requests...", 'CHECK')
        
        missing_columns = []
        for column_name, description in required_columns.items():
            exists = self.check_column_exists('surgery_requests', column_name)
            
            if exists:
                self.log(f"  • {column_name}: OK", 'OK')
            else:
                self.log(f"  • {column_name}: FALTANDO", 'ERROR')
                missing_columns.append(column_name)
        
        return missing_columns
    
    def run_migration(self):
        """Executa alembic upgrade head."""
        self.log("Executando alembic upgrade head...", 'INFO')
        
        try:
            # Mudar para diretório do projeto
            project_root = Path(__file__).parent.parent
            os.chdir(project_root)
            
            # Executar alembic upgrade
            result = subprocess.run(
                [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log("✅ Migração executada com sucesso!", 'OK')
                return True
            else:
                self.log(f"❌ Erro ao executar migração: {result.stderr}", 'ERROR')
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Timeout ao executar alembic upgrade (>30s)", 'ERROR')
            return False
        except Exception as e:
            self.log(f"❌ Erro ao executar migração: {e}", 'ERROR')
            return False
    
    def check_and_migrate(self):
        """Verifica schema e executa migration se necessário."""
        print()
        print("=" * 70)
        print("  VERIFICAÇÃO DE SCHEMA - CIRURGIA AGENDAMENTO")
        print("=" * 70)
        print()
        
        # 1. Verificar colunas
        missing_columns = self.check_surgery_request_columns()
        
        print()
        
        if not missing_columns:
            self.log("✅ Schema está atualizado! Nenhuma migração necessária.", 'OK')
            return True
        
        # 2. Se houver colunas faltando
        self.log(f"⚠️  {len(missing_columns)} coluna(s) faltando: {', '.join(missing_columns)}", 'WARNING')
        print()
        
        # 3. Verificar AUTO_MIGRATE
        auto_migrate = os.getenv('AUTO_MIGRATE', 'false').lower() == 'true'
        
        if auto_migrate:
            self.log("AUTO_MIGRATE=true detectado. Executando migração automática...", 'INFO')
            print()
            
            if self.run_migration():
                print()
                self.log("✅ Schema atualizado com sucesso!", 'OK')
                
                # Verificar novamente
                print()
                missing_columns_after = self.check_surgery_request_columns()
                if not missing_columns_after:
                    print()
                    self.log("✅ Todas as colunas estão presentes!", 'OK')
                    return True
                else:
                    print()
                    self.log(f"❌ Ainda faltam colunas após migração: {missing_columns_after}", 'ERROR')
                    return False
            else:
                print()
                self.log("❌ Falha ao executar migração automática", 'ERROR')
                return False
        else:
            # AUTO_MIGRATE=false: exibir instrução
            print()
            self.log("⚠️  AUTO_MIGRATE não está habilitado", 'WARNING')
            print()
            print("  SOLUÇÃO: Execute a migração manualmente:")
            print()
            print("    alembic upgrade head")
            print()
            print("  OU habilite auto-migração com:")
            print()
            print("    set AUTO_MIGRATE=true")
            print("    python run.py")
            print()
            print("  MAIS INFORMAÇÕES:")
            print("    https://github.com/phgutierrez/patient-registration-system/docs/FIXO_BANCO_DE_DADOS.md")
            print()
            return False


def main():
    """Ponto de entrada principal."""
    verbose = os.getenv('VERBOSE', 'false').lower() == 'true'
    
    checker = SchemaChecker(verbose=verbose)
    success = checker.check_and_migrate()
    
    print()
    print("=" * 70)
    
    if success:
        print("✅ SISTEMA PRONTO!")
        print("=" * 70)
        print()
        return 0
    else:
        print("❌ SISTEMA NÃO ESTÁ PRONTO")
        print("=" * 70)
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
