import os
import sys
import secrets
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _build_google_calendar_ics_url(calendar_id: str) -> str:
    normalized = (calendar_id or '').strip()
    if not normalized:
        return ''
    return f'https://calendar.google.com/calendar/ical/{normalized}/public/basic.ics'


class Config:
    # Detectar se está rodando como executável PyInstaller
    if getattr(sys, 'frozen', False):
        # Se executado como executável, usar o diretório do .exe
        BASE_DIR = Path(sys.executable).parent
    else:
        # Se executado como script Python, usar o diretório do projeto
        BASE_DIR = Path(__file__).resolve().parent.parent

    # Carregar .env do diretório base (prioritário no executável)
    load_dotenv(BASE_DIR / '.env', override=False)
    # Fallback para execução a partir do diretório corrente
    load_dotenv(override=False)
    
    INSTANCE_PATH = BASE_DIR / 'instance'
    INSTANCE_PATH.mkdir(exist_ok=True)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/prontuario.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_DEBUG = _env_bool('FLASK_DEBUG', False)
    _raw_secret_key = (os.getenv('SECRET_KEY') or '').strip()
    _weak_secret_keys = {
        'dev-key-123',
        'patient-reg-secret-key-2026-change-in-production',
        'dev-secret-key-change-in-production-very-long-random-string',
        'chave-secreta-unica-hospital-mude-isso-2026',
        'chave-secreta-unica-hospital-mude-isso-2026-string-aleatoria-muito-longa',
    }

    if not _raw_secret_key:
        SECRET_KEY = secrets.token_hex(32)
    elif _raw_secret_key in _weak_secret_keys and not FLASK_DEBUG:
        raise RuntimeError('SECRET_KEY insegura detectada. Configure uma chave forte no ambiente.')
    else:
        SECRET_KEY = _raw_secret_key

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.getenv('SESSION_IDLE_TIMEOUT_MINUTES', '30')))
    SESSION_REFRESH_EACH_REQUEST = True
    WTF_CSRF_TIME_LIMIT = None
    PROTECTED_PDF_DIR = INSTANCE_PATH / 'protected_pdfs'
    PROTECTED_PDF_DIR.mkdir(exist_ok=True)
    ADMIN_BOOTSTRAP_USERNAME = (os.getenv('ADMIN_BOOTSTRAP_USERNAME') or '').strip()
    ADMIN_BOOTSTRAP_PASSWORD = (os.getenv('ADMIN_BOOTSTRAP_PASSWORD') or '').strip()
    ADMIN_BOOTSTRAP_FULL_NAME = (os.getenv('ADMIN_BOOTSTRAP_FULL_NAME') or 'Administrador do Sistema').strip()
    ADMIN_BOOTSTRAP_SPECIALTY = (os.getenv('ADMIN_BOOTSTRAP_SPECIALTY') or 'ortopedia').strip()
    
    # Auto-migrate database schema on startup (development only)
    AUTO_MIGRATE = _env_bool('AUTO_MIGRATE', False)
    
    # Google Calendar Configuration
    GOOGLE_CALENDAR_ID = (os.getenv('GOOGLE_CALENDAR_ID') or '').strip()
    GOOGLE_CALENDAR_TZ = os.getenv('GOOGLE_CALENDAR_TZ', 'America/Fortaleza')
    GOOGLE_CALENDAR_ICS_URL = (os.getenv('GOOGLE_CALENDAR_ICS_URL') or '').strip()
    ORTOPEDIA_AGENDA_URL = (
        os.getenv('ORTOPEDIA_AGENDA_URL')
        or GOOGLE_CALENDAR_ICS_URL
        or _build_google_calendar_ics_url(GOOGLE_CALENDAR_ID)
    )
    
    # Calendar cache TTL (60 seconds for fast updates)
    CALENDAR_CACHE_TTL_SECONDS = int(os.getenv('CALENDAR_CACHE_TTL_SECONDS', '60'))
    # Legacy minutes setting (deprecated, use seconds instead)
    CALENDAR_CACHE_TTL_MINUTES = int(os.getenv('CALENDAR_CACHE_TTL_MINUTES', '5'))
    
    # Google Forms Configuration (para agendamento automático)
    # IMPORTANTE: Use o ID PÚBLICO do formulário!
    # URL pública: https://docs.google.com/forms/d/e/[ID_PUBLICO]/viewform
    # URL edição: https://docs.google.com/forms/d/[ID_EDICAO]/edit  <- NÃO use este!
    
    # Default embutido fica vazio neste repositório; configure explicitamente via ambiente.
    DEFAULT_GOOGLE_FORMS_PUBLIC_ID = ''
    DEFAULT_GOOGLE_FORMS_VIEWFORM_URL = ''
    
    # Environment overrides (optional)
    GOOGLE_FORMS_EDIT_ID = (os.getenv('GOOGLE_FORMS_EDIT_ID') or '').strip()
    GOOGLE_FORMS_PUBLIC_ID = (os.getenv('GOOGLE_FORMS_PUBLIC_ID') or DEFAULT_GOOGLE_FORMS_PUBLIC_ID).strip()
    GOOGLE_FORMS_VIEWFORM_URL = (os.getenv('GOOGLE_FORMS_VIEWFORM_URL') or DEFAULT_GOOGLE_FORMS_VIEWFORM_URL).strip()
    GOOGLE_FORMS_TIMEOUT = int(os.getenv('GOOGLE_FORMS_TIMEOUT', '10'))

    # Browser-facing response hardening
    SECURITY_HEADERS_ENABLED = _env_bool('SECURITY_HEADERS_ENABLED', True)
    SECURITY_CSP_REPORT_ONLY = _env_bool('SECURITY_CSP_REPORT_ONLY', True)
    SECURITY_CSP_REPORT_URI = (os.getenv('SECURITY_CSP_REPORT_URI') or '').strip()
    SECURITY_CSP_REPORT_ONLY_POLICY = os.getenv(
        'SECURITY_CSP_REPORT_ONLY_POLICY',
        "default-src 'self'; frame-ancestors 'none'; object-src 'none'; "
        "base-uri 'self'; form-action 'self'; img-src 'self' data:; "
        "font-src 'self' https: data:; frame-src 'self' https://docs.google.com; "
        "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https:; "
        "connect-src 'self' https://docs.google.com https://calendar.google.com",
    )
    SECURITY_HSTS_ENABLED = _env_bool('SECURITY_HSTS_ENABLED', False)
    SECURITY_HSTS_MAX_AGE_SECONDS = int(os.getenv('SECURITY_HSTS_MAX_AGE_SECONDS', '31536000'))
    SECURITY_HSTS_INCLUDE_SUBDOMAINS = _env_bool('SECURITY_HSTS_INCLUDE_SUBDOMAINS', True)
    SECURITY_HSTS_PRELOAD = _env_bool('SECURITY_HSTS_PRELOAD', False)

    # Server Configuration
    SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')  # 0.0.0.0 for LAN
    SERVER_PORT = int(os.getenv('SERVER_PORT', '5000'))
    
    # Desktop lifecycle / auto-shutdown (only for desktop mode)
    DESKTOP_MODE = _env_bool('DESKTOP_MODE', False)
    LIFECYCLE_TIMEOUT_SECONDS = int(os.getenv('LIFECYCLE_TIMEOUT_SECONDS', '30'))
    LIFECYCLE_HEARTBEAT_SECONDS = int(os.getenv('LIFECYCLE_HEARTBEAT_SECONDS', '5'))
    SERVER_BIND_HOST = os.getenv('SERVER_BIND_HOST', SERVER_HOST)  # Backward compatibility
    
    # Apps Script Web App (DESABILITADO - agora usa submissão ao Forms)
    # APPS_SCRIPT_SCHEDULER_URL = os.getenv('APPS_SCRIPT_SCHEDULER_URL', None)
