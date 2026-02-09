import os
import sys
from pathlib import Path

class Config:
    # Detectar se está rodando como executável PyInstaller
    if getattr(sys, 'frozen', False):
        # Se executado como executável, usar o diretório do .exe
        BASE_DIR = Path(sys.executable).parent
    else:
        # Se executado como script Python, usar o diretório do projeto
        BASE_DIR = Path(__file__).resolve().parent.parent
    
    INSTANCE_PATH = BASE_DIR / 'instance'
    INSTANCE_PATH.mkdir(exist_ok=True)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{INSTANCE_PATH}/prontuario.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    
    # Auto-migrate database schema on startup (development only)
    AUTO_MIGRATE = os.getenv('AUTO_MIGRATE', 'false').lower() == 'true'
    
    # Google Calendar Configuration
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 's4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com')
    GOOGLE_CALENDAR_TZ = os.getenv('GOOGLE_CALENDAR_TZ', 'America/Fortaleza')
    GOOGLE_CALENDAR_ICS_URL = os.getenv('GOOGLE_CALENDAR_ICS_URL', None)  # Se None, será construído
    
    # Calendar cache TTL (60 seconds for fast updates)
    CALENDAR_CACHE_TTL_SECONDS = int(os.getenv('CALENDAR_CACHE_TTL_SECONDS', '60'))
    # Legacy minutes setting (deprecated, use seconds instead)
    CALENDAR_CACHE_TTL_MINUTES = int(os.getenv('CALENDAR_CACHE_TTL_MINUTES', '5'))
    
    # Google Forms Configuration (para agendamento automático)
    # IMPORTANTE: Use o ID PÚBLICO do formulário!
    # URL pública: https://docs.google.com/forms/d/e/[ID_PUBLICO]/viewform
    # URL edição: https://docs.google.com/forms/d/[ID_EDICAO]/edit  <- NÃO use este!
    GOOGLE_FORMS_EDIT_ID = os.getenv('GOOGLE_FORMS_EDIT_ID', '1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw')
    GOOGLE_FORMS_PUBLIC_ID = os.getenv('GOOGLE_FORMS_PUBLIC_ID', None)
    # URL pública do Forms (opcional) - ex: https://docs.google.com/forms/d/e/<PUBLIC_ID>/viewform
    GOOGLE_FORMS_VIEWFORM_URL = os.getenv('GOOGLE_FORMS_VIEWFORM_URL', None)
    GOOGLE_FORMS_TIMEOUT = int(os.getenv('GOOGLE_FORMS_TIMEOUT', '10'))

    # Server Configuration
    SERVER_HOST = os.getenv('SERVER_HOST', '127.0.0.1')  # 0.0.0.0 for LAN
    SERVER_PORT = int(os.getenv('SERVER_PORT', '5000'))
    
    # Desktop lifecycle / auto-shutdown (only for desktop mode)
    DESKTOP_MODE = os.getenv('DESKTOP_MODE', 'false').lower() == 'true'
    LIFECYCLE_TIMEOUT_SECONDS = int(os.getenv('LIFECYCLE_TIMEOUT_SECONDS', '30'))
    LIFECYCLE_HEARTBEAT_SECONDS = int(os.getenv('LIFECYCLE_HEARTBEAT_SECONDS', '5'))
    SERVER_BIND_HOST = os.getenv('SERVER_BIND_HOST', SERVER_HOST)  # Backward compatibility
    
    # Apps Script Web App (DESABILITADO - agora usa submissão ao Forms)
    # APPS_SCRIPT_SCHEDULER_URL = os.getenv('APPS_SCRIPT_SCHEDULER_URL', None)
