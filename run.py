from src.app import app
import signal
import sys
import logging
import atexit
import os


def check_and_auto_migrate():
    """Verifica se migrations estão aplicadas e executa se AUTO_MIGRATE=true."""
    auto_migrate = os.getenv('AUTO_MIGRATE', 'false').lower() == 'true'
    
    if not auto_migrate:
        return
    
    try:
        # Importar função de check
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from scripts.check_and_migrate_schema import SchemaChecker
        
        checker = SchemaChecker(verbose=False)
        
        # Verificar schema
        missing = checker.check_surgery_request_columns()
        
        if missing:
            print()
            print("⚠️  Colunas faltando no banco de dados. Executando AUTO_MIGRATE...")
            print()
            
            if checker.run_migration():
                print("✅ Migração concluída com sucesso!")
            else:
                print("❌ Falha ao executar migração automática")
                print("   Execute manualmente: alembic upgrade head")
        
    except Exception as e:
        print(f"⚠️  Erro ao verificar schema: {e}")
        print("   Execute manualmente: alembic upgrade head")


def signal_handler(sig, frame):
    print('\nDesligando o servidor...')
    logging.shutdown()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(logging.shutdown)
    
    # Verificar e executar auto-migração se necessário
    check_and_auto_migrate()
    
    app.run(debug=True, host='0.0.0.0', port=5000)

