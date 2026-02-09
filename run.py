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
    
    # Check if we should use production server instead
    use_waitress = os.getenv('USE_WAITRESS', 'false').lower() == 'true'
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    host = os.getenv('SERVER_HOST', '127.0.0.1')
    port = int(os.getenv('SERVER_PORT', '5000'))
    
    if use_waitress:
        print("\\n" + "="*50)
        print("🚀 Starting Patient Registration System")
        print("="*50)
        print(f"Server: Waitress (production)")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"Debug: {'ON' if debug_mode else 'OFF'}")
        print(f"Desktop Mode: {os.getenv('DESKTOP_MODE', 'false')}")
        print("="*50)
        print(f"Access: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        if host == '0.0.0.0':
            print("Network access: http://YOUR_IP_ADDRESS:" + str(port))
        print("Press Ctrl+C to stop")
        print("="*50 + "\\n")
        
        try:
            from waitress import serve
            serve(app, host=host, port=port)
        except ImportError:
            print("ERROR: Waitress not installed. Install with: pip install waitress")
            print("Falling back to Flask dev server...")
            app.run(debug=debug_mode, host=host, port=port)
    else:
        print("\\n" + "="*50)
        print("⚠️  DEVELOPMENT MODE")
        print("="*50)
        print("Using Flask development server")
        print("For production use: set USE_WAITRESS=true")
        print("Or use: run_network.bat / run_local.bat")
        print("="*50 + "\\n")
        
        # Flask development server (only for development)
        app.run(debug=debug_mode, host=host, port=port)

