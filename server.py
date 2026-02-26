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

def get_base_dir():
    """Retorna o diretório base correto, mesmo quando empacotado com PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Se executado como executável PyInstaller
        # Usa o diretório onde o .exe está localizado, não o temporário
        return os.path.dirname(sys.executable)
    else:
        # Se executado como script Python normal
        return os.path.dirname(os.path.abspath(__file__))

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

def create_initial_users(app):
    """Cria usuários iniciais se o banco estiver vazio"""
    with app.app_context():
        from src.extensions import db
        from src.models.user import User
        
        # Verificar se já existem usuários
        user_count = User.query.count()
        
        if user_count == 0:
            logger.info('Criando usuários iniciais...')
            
            users_data = [
                {'username': 'pedro', 'full_name': 'Pedro Freitas', 'cns': None, 'crm': None},
                {'username': 'andre', 'full_name': 'André Cristiano', 'cns': None, 'crm': None},
                {'username': 'brauner', 'full_name': 'Brauner Cavalcanti', 'cns': None, 'crm': None},
                {'username': 'savio', 'full_name': 'Sávio Bruno', 'cns': None, 'crm': None},
                {'username': 'laecio', 'full_name': 'Laecio Damaceno', 'cns': None, 'crm': None},
            ]
            
            for user_data in users_data:
                user = User(
                    username=user_data['username'],
                    password='123456',  # Senha padrão
                    full_name=user_data['full_name'],
                    cns=user_data['cns'],
                    crm=user_data['crm'],
                    role='solicitante'
                )
                db.session.add(user)
                logger.info(f'  ✓ Usuário criado: {user_data["full_name"]}')
            
            db.session.commit()
            logger.info('=' * 60)
            logger.info('✅ Usuários iniciais criados com sucesso!')
            logger.info('   Usuários: Pedro, André, Brauner, Sávio, Laecio')
            logger.info('   Senha padrão: 123456')
            logger.info('=' * 60)
        else:
            logger.info(f'Banco já possui {user_count} usuário(s) cadastrado(s)')

def initialize_app():
    """Inicializa a aplicação Flask com tratamento de erros"""
    try:
        # Definir o diretório base antes de importar app
        base_dir = get_base_dir()
        
        # Configurar caminhos para instance e PDFs
        instance_path = os.path.join(base_dir, 'instance')
        pdf_dir = os.path.join(base_dir, 'src', 'static', 'pdfs', 'gerados')
        
        # Criar diretórios se não existirem
        os.makedirs(instance_path, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Configurar variável de ambiente para o Flask encontrar o instance folder
        os.environ['INSTANCE_PATH'] = instance_path
        
        from src.app import app
        
        logger.info(f'Diretório base: {base_dir}')
        logger.info(f'Diretório de instance: {instance_path}')
        logger.info(f'Diretório de PDFs: {pdf_dir}')
        
        # Inicializar banco de dados se necessário
        with app.app_context():
            from src.extensions import db
            # Importar todos os modelos antes de criar as tabelas
            from src.models.user import User
            from src.models.patient import Patient
            from src.models.surgery_request import SurgeryRequest
            
            try:
                # Criar tabelas se não existirem
                db.create_all()
                logger.info('Banco de dados inicializado')
            except Exception as e:
                logger.error(f'Erro ao inicializar banco de dados: {e}')
                logger.warning('Continuando sem banco de dados...')
        
        # Criar usuários iniciais se necessário
        try:
            create_initial_users(app)
        except Exception as e:
            logger.error(f'Erro ao criar usuários iniciais: {e}')
            logger.warning('Continuando sem usuários iniciais...')
        
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
