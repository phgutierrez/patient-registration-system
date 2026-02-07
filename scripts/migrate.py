"""
Script helper para aplicar migrations - atalho conveniente

USO:
    python scripts/migrate.py
    
    Ou com argumentos:
    python scripts/migrate.py --revision head
    python scripts/migrate.py --current
    python scripts/migrate.py --history
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Executa comando e exibe resultado."""
    print()
    print(f"▶️  {description}...")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print()
            print(f"✅ {description} concluído com sucesso!")
            return True
        else:
            print()
            print(f"❌ Erro ao {description.lower()}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def main():
    """Menu principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Helper script para migrations com Alembic'
    )
    parser.add_argument(
        '--revision',
        default='head',
        help='Revision para upgrade (default: head)'
    )
    parser.add_argument(
        '--current',
        action='store_true',
        help='Mostrar revision atual'
    )
    parser.add_argument(
        '--history',
        action='store_true',
        help='Mostrar histórico de revisions'
    )
    parser.add_argument(
        '--downgrade',
        action='store_true',
        help='Fazer downgrade de uma revision'
    )
    
    args = parser.parse_args()
    
    print()
    print("=" * 70)
    print("  HELPER DE MIGRATIONS - ALEMBIC")
    print("=" * 70)
    
    # Mudar para diretório raiz
    project_root = Path(__file__).parent.parent
    import os
    os.chdir(project_root)
    
    if args.current:
        run_command('alembic current', 'Obtendo revision atual')
    elif args.history:
        run_command('alembic history --verbose', 'Obtendo histórico de revisions')
    elif args.downgrade:
        run_command('alembic downgrade -1', 'Fazendo downgrade de uma revision')
    else:
        # Default: upgrade to head
        run_command(
            f'alembic upgrade {args.revision}',
            f'Aplicando migrations até {args.revision}'
        )
    
    print()
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
