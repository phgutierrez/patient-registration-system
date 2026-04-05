"""
Servidor de produção usando Waitress
"""
from waitress import serve
import os
import logging
import secrets
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

DEFAULT_CALENDAR_ID = ''
DEFAULT_CALENDAR_TZ = 'America/Fortaleza'


def build_default_ortopedia_agenda_url(calendar_id: str) -> str:
    cid = (calendar_id or '').strip()
    if not cid:
        return ''
    return f'https://calendar.google.com/calendar/ical/{cid}/public/basic.ics'


def ensure_env_file(base_dir: str):
    """Cria .env com defaults seguros quando não existir (útil no executável)."""
    env_path = os.path.join(base_dir, '.env')
    if os.path.exists(env_path):
        return

    calendar_id = (os.getenv('GOOGLE_CALENDAR_ID') or DEFAULT_CALENDAR_ID).strip()
    calendar_tz = os.getenv('GOOGLE_CALENDAR_TZ', DEFAULT_CALENDAR_TZ)
    ortopedia_agenda_url = (
        os.getenv('ORTOPEDIA_AGENDA_URL')
        or os.getenv('GOOGLE_CALENDAR_ICS_URL')
        or build_default_ortopedia_agenda_url(calendar_id)
    )
    forms_edit_id = (os.getenv('GOOGLE_FORMS_EDIT_ID') or '').strip()
    forms_public_id = (os.getenv('GOOGLE_FORMS_PUBLIC_ID') or '').strip()
    forms_viewform_url = (os.getenv('GOOGLE_FORMS_VIEWFORM_URL') or '').strip()

    generated_secret = secrets.token_hex(32)

    content = f"""# =================================================================
# Patient Registration System - Configuracao do Ambiente
# Gerado automaticamente pelo executavel
# =================================================================

SECRET_KEY={generated_secret}
FLASK_ENV=production
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
SESSION_IDLE_TIMEOUT_MINUTES=30
SERVER_HOST=127.0.0.1
SERVER_PORT=5000
DESKTOP_MODE=true
GOOGLE_CALENDAR_ID={calendar_id}
GOOGLE_CALENDAR_TZ={calendar_tz}
GOOGLE_CALENDAR_ICS_URL={ortopedia_agenda_url}
ORTOPEDIA_AGENDA_URL={ortopedia_agenda_url}
CALENDAR_CACHE_TTL_SECONDS=60
CALENDAR_CACHE_TTL_MINUTES=5
GOOGLE_FORMS_EDIT_ID={forms_edit_id}
GOOGLE_FORMS_PUBLIC_ID={forms_public_id}
GOOGLE_FORMS_VIEWFORM_URL={forms_viewform_url}
GOOGLE_FORMS_TIMEOUT=10
SECURITY_HEADERS_ENABLED=true
SECURITY_CSP_REPORT_ONLY=true
SECURITY_CSP_REPORT_URI=
SECURITY_HSTS_ENABLED=false
SECURITY_HSTS_MAX_AGE_SECONDS=31536000
SECURITY_HSTS_INCLUDE_SUBDOMAINS=true
SECURITY_HSTS_PRELOAD=false
LIFECYCLE_TIMEOUT_SECONDS=30
LIFECYCLE_HEARTBEAT_SECONDS=5
ADMIN_BOOTSTRAP_USERNAME=
ADMIN_BOOTSTRAP_PASSWORD=
ADMIN_BOOTSTRAP_FULL_NAME=Administrador do Sistema
ADMIN_BOOTSTRAP_SPECIALTY=ortopedia
"""
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Arquivo .env criado automaticamente em: {env_path}")

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

def create_initial_data(app):
    """Cria dados iniciais mínimos (especialidades/settings/usuários) se ausentes."""
    with app.app_context():
        from src.extensions import db
        from src.models.user import User
        from src.models.specialty import Specialty, SpecialtySettings, SpecialtyProcedure
        from src.services.default_seed_data import ORTOPEDIA_PROCEDURES
        from src.runtime_security import bootstrap_admin_if_configured

        # Especialidades padrão
        ortopedia = Specialty.query.filter_by(slug='ortopedia').first()
        cirurgia = Specialty.query.filter_by(slug='cirurgia_pediatrica').first()
        if not ortopedia:
            ortopedia = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            db.session.add(ortopedia)
            logger.info('  [OK] Especialidade criada: Ortopedia')
        if not cirurgia:
            cirurgia = Specialty(slug='cirurgia_pediatrica', name='Cirurgia Pediatrica', is_active=True)
            db.session.add(cirurgia)
            logger.info('  [OK] Especialidade criada: Cirurgia Pediatrica')
        db.session.flush()

        # Configuração inicial da agenda de Ortopedia
        ortopedia_agenda_url = (
            os.getenv('ORTOPEDIA_AGENDA_URL')
            or os.getenv('GOOGLE_CALENDAR_ICS_URL')
            or build_default_ortopedia_agenda_url(os.getenv('GOOGLE_CALENDAR_ID', DEFAULT_CALENDAR_ID))
        )
        ortopedia_forms_url = (os.getenv('GOOGLE_FORMS_VIEWFORM_URL') or '').strip()

        ortopedia_settings = SpecialtySettings.query.filter_by(specialty_id=ortopedia.id).first()
        if not ortopedia_settings:
            db.session.add(SpecialtySettings(
                specialty_id=ortopedia.id,
                agenda_url=ortopedia_agenda_url,
                forms_url=ortopedia_forms_url,
            ))
            logger.info('  [OK] Configuração criada: agenda/formulário da Ortopedia')
        elif not (ortopedia_settings.agenda_url or '').strip() and ortopedia_agenda_url:
            ortopedia_settings.agenda_url = ortopedia_agenda_url
            logger.info('  [OK] Configuração atualizada: agenda padrão da Ortopedia')

        cirurgia_settings = SpecialtySettings.query.filter_by(specialty_id=cirurgia.id).first()
        if not cirurgia_settings:
            db.session.add(SpecialtySettings(
                specialty_id=cirurgia.id,
                agenda_url='',
                forms_url='',
            ))
            logger.info('  [OK] Configuração criada: Cirurgia Pediatrica')

        # Procedimentos padrão de Ortopedia
        ortopedia_proc_count = SpecialtyProcedure.query.filter_by(specialty_id=ortopedia.id).count()
        if ortopedia_proc_count == 0:
            for i, (descricao, codigo_sus) in enumerate(ORTOPEDIA_PROCEDURES):
                db.session.add(SpecialtyProcedure(
                    specialty_id=ortopedia.id,
                    descricao=descricao,
                    codigo_sus=codigo_sus,
                    is_active=True,
                    sort_order=i,
                ))
            logger.info(f'  [OK] Procedimentos de Ortopedia criados: {len(ORTOPEDIA_PROCEDURES)}')

        # Verificar se já existem usuários
        user_count = User.query.count()

        if user_count == 0:
            logger.info('Nenhum usuário padrão inseguro será criado automaticamente.')
            db.session.commit()
            bootstrap_admin_if_configured(app)
            logger.info('Configure ADMIN_BOOTSTRAP_USERNAME e ADMIN_BOOTSTRAP_PASSWORD para semear o primeiro administrador.')
        else:
            # Backfill para instalações antigas: garantir vínculo com especialidade
            usuarios_sem_especialidade = User.query.filter(User.specialty_id.is_(None)).all()
            if usuarios_sem_especialidade:
                for user in usuarios_sem_especialidade:
                    user.specialty_id = ortopedia.id
                logger.info(f'  [OK] Usuários atualizados com especialidade Ortopedia: {len(usuarios_sem_especialidade)}')

            db.session.commit()
            logger.info(f'Banco já possui {user_count} usuário(s) cadastrado(s)')

def initialize_app():
    """Inicializa a aplicação Flask com tratamento de erros"""
    try:
        # Definir o diretório base antes de importar app
        base_dir = get_base_dir()
        ensure_env_file(base_dir)
        
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
            import src.models  # noqa: F401
            
            try:
                # Criar tabelas se não existirem
                db.create_all()
                logger.info('Banco de dados inicializado')
            except Exception as e:
                logger.error(f'Erro ao inicializar banco de dados: {e}')
                logger.warning('Continuando sem banco de dados...')
        
        # Criar dados iniciais se necessário
        try:
            create_initial_data(app)
        except Exception as e:
            logger.error(f'Erro ao criar dados iniciais: {e}')
            logger.warning('Continuando sem dados iniciais...')
        
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
        
        # Compatível com run_local.bat (.env usa SERVER_HOST/SERVER_PORT)
        host = os.getenv('SERVER_HOST') or os.getenv('HOST', '127.0.0.1')
        port = int(os.getenv('SERVER_PORT') or os.getenv('PORT', 5000))

        # Em executável desktop, manter comportamento local por padrão
        if getattr(sys, 'frozen', False) and 'DESKTOP_MODE' not in os.environ:
            os.environ['DESKTOP_MODE'] = 'true'
        
        logger.info('=' * 60)
        logger.info('Patient Registration System')
        logger.info('=' * 60)
        logger.info(f'Iniciando servidor em http://{host}:{port}')
        logger.info(f"Desktop Mode: {os.getenv('DESKTOP_MODE', 'false')}")
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
