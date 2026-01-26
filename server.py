"""
Servidor de produção usando Waitress
"""
from waitress import serve
from src.app import app
import os
import logging
import signal
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

def main():
    """Inicia o servidor com Waitress"""
    # Registrar handlers de sinal
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f'Iniciando servidor em http://{host}:{port}')
    logger.info('Pressione CTRL+C para parar o servidor')
    logger.info('Ou use o botão "Sair do Sistema" na interface')
    
    try:
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
        logger.info('Servidor interrompido pelo usuário')
    except Exception as e:
        logger.error(f'Erro no servidor: {e}')
    finally:
        logger.info('Servidor encerrado')

if __name__ == '__main__':
    main()
