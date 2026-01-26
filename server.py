"""
Servidor de produção usando Waitress
"""
from waitress import serve
import os
import logging
import signal
import sys
import webbrowser
import threading
import time

# Configurar logging com mais detalhes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Variável global para controlar o servidor
server_running = True

def signal_handler(signum, frame):
    """Handler para sinais de término"""
    global server_running
    logger.info('Recebido sinal de término. Encerrando servidor...')
    server_running = False
    sys.exit(0)

def open_browser(host, port, delay=2):
    """Abre o navegador após o servidor iniciar"""
    time.sleep(delay)
    url = f'http://{host}:{port}'
    logger.info(f'Abrindo navegador em {url}')
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.warning(f'Não foi possível abrir o navegador automaticamente: {e}')

def initialize_app():
    """Inicializa a aplicação Flask com tratamento de erros"""
    try:
        from src.app import app
        
        # Garantir que o diretório de PDFs existe
        pdf_dir = os.path.join(os.path.dirname(__file__), 'src', 'static', 'pdfs', 'gerados')
        os.makedirs(pdf_dir, exist_ok=True)
        logger.info(f'Diretório de PDFs verificado: {pdf_dir}')
        
        # Inicializar banco de dados se necessário
        with app.app_context():
            from src.extensions import db
            try:
                # Criar tabelas se não existirem
                db.create_all()
                logger.info('Banco de dados inicializado')
            except Exception as e:
                logger.error(f'Erro ao inicializar banco de dados: {e}')
                logger.warning('Continuando sem banco de dados...')
        
        return app
    except Exception as e:
        logger.error(f'Erro ao inicializar aplicação: {e}', exc_info=True)
        raise

def main():
    """Inicia o servidor com Waitress"""
    try:
        # Registrar handlers de sinal
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        host = os.getenv('HOST', '127.0.0.1')
        port = int(os.getenv('PORT', 5000))
        
        logger.info('=' * 60)
        logger.info('Patient Registration System')
        logger.info('=' * 60)
        logger.info(f'Iniciando servidor em http://{host}:{port}')
        logger.info('Pressione CTRL+C para parar o servidor')
        logger.info('Ou use o botão "Sair do Sistema" na interface')
        logger.info('=' * 60)
        
        # Inicializar aplicação
        app = initialize_app()
        
        # Abrir navegador em thread separada
        browser_thread = threading.Thread(target=open_browser, args=(host, port), daemon=True)
        browser_thread.start()
        
        # Servir a aplicação com Waitress
        serve(
            app,
            host=host,
            port=port,
            threads=4,  # Número de threads para processar requisições
            channel_timeout=120,
            cleanup_interval=30,
            url_scheme='http'
        )
    except KeyboardInterrupt:
        logger.info('\nServidor interrompido pelo usuário')
    except Exception as e:
        logger.error(f'Erro no servidor: {e}', exc_info=True)
        input('\nPressione ENTER para sair...')
    finally:
        logger.info('Servidor encerrado')

if __name__ == '__main__':
    main()
