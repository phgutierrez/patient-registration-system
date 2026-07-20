"""
Servidor de produção usando Waitress
"""
from waitress.server import create_server
import argparse
import os
import logging
from logging.handlers import RotatingFileHandler
import secrets
import signal
import sys
import webbrowser
import threading
import time
import socket
import urllib.request
import uuid
from dotenv import dotenv_values, set_key
from src.default_integrations import (
    DEFAULT_CALENDAR_ID, DEFAULT_CALENDAR_TZ, DEFAULT_CALENDAR_ICS_URL,
    DEFAULT_FORMS_EDIT_ID, DEFAULT_FORMS_PUBLIC_ID, DEFAULT_FORMS_VIEW_URL,
    PUBLIC_ENV_DEFAULTS, calendar_ics_url, forms_view_url,
)

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

def configure_file_logging(base_dir: str) -> str:
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'patient-registration.log')
    root_logger = logging.getLogger()
    if not any(isinstance(handler, RotatingFileHandler) for handler in root_logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(handler)
    return log_path


def build_default_ortopedia_agenda_url(calendar_id: str) -> str:
    return calendar_ics_url(calendar_id)


def _fill_blank_public_env_defaults(env_path: str) -> None:
    current = dotenv_values(env_path)
    calendar_id = str(current.get('GOOGLE_CALENDAR_ID') or os.getenv('GOOGLE_CALENDAR_ID') or DEFAULT_CALENDAR_ID).strip()
    calendar_url = str(current.get('GOOGLE_CALENDAR_ICS_URL') or os.getenv('GOOGLE_CALENDAR_ICS_URL') or calendar_ics_url(calendar_id)).strip()
    forms_public_id = str(current.get('GOOGLE_FORMS_PUBLIC_ID') or os.getenv('GOOGLE_FORMS_PUBLIC_ID') or DEFAULT_FORMS_PUBLIC_ID).strip()
    effective_defaults = {
        **PUBLIC_ENV_DEFAULTS,
        'GOOGLE_CALENDAR_ID': calendar_id,
        'GOOGLE_CALENDAR_ICS_URL': calendar_url,
        'ORTOPEDIA_AGENDA_URL': str(os.getenv('ORTOPEDIA_AGENDA_URL') or calendar_url).strip(),
        'GOOGLE_FORMS_PUBLIC_ID': forms_public_id,
        'GOOGLE_FORMS_VIEWFORM_URL': str(os.getenv('GOOGLE_FORMS_VIEWFORM_URL') or forms_view_url(forms_public_id)).strip(),
    }
    updated = []
    for key, default in effective_defaults.items():
        if not str(current.get(key) or '').strip():
            effective_default = str(os.getenv(key) or default).strip()
            set_key(env_path, key, effective_default, quote_mode='never')
            os.environ[key] = effective_default
            updated.append(key)
    if updated:
        logger.info('Defaults públicos aplicados ao .env: %s', ', '.join(updated))


def ensure_env_file(base_dir: str):
    """Cria .env com defaults seguros quando não existir (útil no executável)."""
    env_path = os.path.join(base_dir, '.env')
    if os.path.exists(env_path):
        _fill_blank_public_env_defaults(env_path)
        return

    calendar_id = (os.getenv('GOOGLE_CALENDAR_ID') or DEFAULT_CALENDAR_ID).strip()
    calendar_tz = os.getenv('GOOGLE_CALENDAR_TZ', DEFAULT_CALENDAR_TZ)
    ortopedia_agenda_url = (
        os.getenv('ORTOPEDIA_AGENDA_URL')
        or os.getenv('GOOGLE_CALENDAR_ICS_URL')
        or build_default_ortopedia_agenda_url(calendar_id)
    )
    forms_edit_id = (os.getenv('GOOGLE_FORMS_EDIT_ID') or DEFAULT_FORMS_EDIT_ID).strip()
    forms_public_id = (os.getenv('GOOGLE_FORMS_PUBLIC_ID') or DEFAULT_FORMS_PUBLIC_ID).strip()
    forms_viewform_url = (os.getenv('GOOGLE_FORMS_VIEWFORM_URL') or forms_view_url(forms_public_id)).strip()

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

def open_browser(host, port, session_id=None, timeout=30):
    """Espera a aplicação responder antes de abrir o navegador."""
    health_url = f'http://127.0.0.1:{port}/health'
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(0.4)
    else:
        logger.error('Servidor não respondeu em %s segundos; navegador não será aberto.', timeout)
        return
    url = f'http://127.0.0.1:{port}/'
    if session_id:
        url += f'?session={session_id}'
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
        if not ortopedia:
            ortopedia = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            db.session.add(ortopedia)
            logger.info('  [OK] Especialidade criada: Ortopedia')
        db.session.flush()

        # Configuração inicial da agenda de Ortopedia
        ortopedia_agenda_url = (
            os.getenv('ORTOPEDIA_AGENDA_URL')
            or os.getenv('GOOGLE_CALENDAR_ICS_URL')
            or build_default_ortopedia_agenda_url(os.getenv('GOOGLE_CALENDAR_ID') or DEFAULT_CALENDAR_ID)
        )
        ortopedia_forms_url = (os.getenv('GOOGLE_FORMS_VIEWFORM_URL') or DEFAULT_FORMS_VIEW_URL).strip()

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
        if ortopedia_settings and not (ortopedia_settings.forms_url or '').strip() and ortopedia_forms_url:
            ortopedia_settings.forms_url = ortopedia_forms_url
            logger.info('  [OK] Configuração atualizada: formulário padrão da Ortopedia')

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

def initialize_app(base_dir=None):
    """Inicializa a aplicação Flask com tratamento de erros"""
    try:
        # Definir o diretório base antes de importar app
        base_dir = base_dir or get_base_dir()
        os.environ['APP_DATA_DIR'] = base_dir
        ensure_env_file(base_dir)
        log_path = configure_file_logging(base_dir)
        
        # Configurar caminhos para instance e PDFs
        instance_path = os.path.join(base_dir, 'instance')
        
        # Criar diretórios se não existirem
        os.makedirs(instance_path, exist_ok=True)
        
        # Configurar variável de ambiente para o Flask encontrar o instance folder
        os.environ['INSTANCE_PATH'] = instance_path
        
        from src.app import app
        
        logger.info(f'Diretório base: {base_dir}')
        logger.info(f'Diretório de instance: {instance_path}')
        logger.info(f'Arquivo de log: {log_path}')
        
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
                raise
        
        # Criar dados iniciais se necessário
        try:
            create_initial_data(app)
        except Exception as e:
            logger.error(f'Erro ao criar dados iniciais: {e}')
            raise
        
        return app
    except Exception as e:
        logger.error(f'Erro ao inicializar aplicação: {e}', exc_info=True)
        raise

def _port_is_available(host: str, port: int) -> bool:
    probe_host = '0.0.0.0' if host == '0.0.0.0' else host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((probe_host, port))
        return True
    except OSError:
        return False


def _parse_args():
    parser = argparse.ArgumentParser(description='Inicializador do Patient Registration System')
    parser.add_argument('--mode', choices=('local', 'network'), default='local')
    parser.add_argument('--check', action='store_true', help='Valida e inicializa sem abrir o servidor')
    parser.add_argument('--self-check', action='store_true', help='Smoke test usado pelo executável')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--data-dir', help='Diretório de dados alternativo para testes')
    return parser.parse_args()


def _apply_mode(mode: str) -> tuple[str, int]:
    if mode == 'network':
        os.environ['SERVER_HOST'] = '0.0.0.0'
        os.environ['DESKTOP_MODE'] = 'false'
    else:
        os.environ['SERVER_HOST'] = '127.0.0.1'
        os.environ['DESKTOP_MODE'] = 'true'
    os.environ.setdefault('SERVER_PORT', '5000')
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = '0'
    return os.environ['SERVER_HOST'], int(os.environ['SERVER_PORT'])


def main():
    """Inicia o servidor com Waitress"""
    try:
        args = _parse_args()
        host, port = _apply_mode(args.mode)
        if args.check or args.self_check:
            os.environ['DESKTOP_MODE'] = 'false'
        base_dir = os.path.abspath(args.data_dir) if args.data_dir else get_base_dir()
        os.makedirs(base_dir, exist_ok=True)
        write_probe = os.path.join(base_dir, '.write-test.tmp')
        try:
            with open(write_probe, 'w', encoding='utf-8') as probe:
                probe.write('ok')
            os.unlink(write_probe)
        except OSError as exc:
            raise RuntimeError(f'A pasta do programa não permite escrita: {base_dir} ({exc})') from exc

        # Registrar handlers de sinal
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.info('=' * 60)
        logger.info('Patient Registration System')
        logger.info('=' * 60)
        logger.info(f'Iniciando servidor em http://{host}:{port}')
        logger.info(f"Desktop Mode: {os.getenv('DESKTOP_MODE', 'false')}")
        logger.info('Pressione CTRL+C para parar o servidor')
        logger.info('Ou use o botão "Sair do Sistema" na interface')
        logger.info('=' * 60)
        
        # Inicializar aplicação
        app = initialize_app(base_dir)

        if args.check or args.self_check:
            with app.test_client() as client:
                response = client.get('/health')
                if response.status_code != 200:
                    raise RuntimeError(f'Autoverificação HTTP falhou: {response.status_code}')
            logger.info('Autoverificação concluída com sucesso.')
            if args.self_check and getattr(sys, 'frozen', False):
                logging.shutdown()
                os._exit(0)
            return 0

        if not _port_is_available(host, port):
            raise RuntimeError(f'A porta {port} já está em uso. Encerre a outra instância ou processo.')
        
        # Abrir navegador em thread separada
        if not args.no_browser:
            session_id = str(uuid.uuid4()) if args.mode == 'local' else None
            threading.Thread(
                target=open_browser, args=(host, port, session_id), daemon=True
            ).start()
        
        # Servir com uma instância controlável para shutdown gracioso.
        from src.services.server_control import server_controller
        from src.services.access_patient_service import access_patient_service
        from src.extensions import db

        waitress_server = create_server(
            app,
            host=host,
            port=port,
            threads=4,  # Número de threads para processar requisições
            channel_timeout=120,
            cleanup_interval=30,
            asyncore_loop_timeout=1,
            url_scheme='http'
        )
        def cleanup_services():
            access_patient_service.invalidate()
            with app.app_context():
                db.session.remove()

        server_controller.register(
            waitress_server,
            cleanup_services,
            allow_force_exit=getattr(sys, 'frozen', False),
        )
        try:
            waitress_server.run()
        finally:
            server_controller.mark_stopped()
    except KeyboardInterrupt:
        logger.info('\nServidor interrompido pelo usuário')
    except Exception as e:
        logger.error(f'Erro no servidor: {e}', exc_info=True)
        if getattr(sys, 'frozen', False) and os.getenv('PATIENT_REGISTRATION_NO_DIALOG') != '1':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(None, str(e), 'Patient Registration - Erro', 0x10)
            except Exception:
                pass
        return 1
    finally:
        logger.info('Servidor encerrado')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
