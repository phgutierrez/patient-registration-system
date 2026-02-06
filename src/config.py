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
    
    # Google Calendar Configuration
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 's4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com')
    GOOGLE_CALENDAR_TZ = os.getenv('GOOGLE_CALENDAR_TZ', 'America/Fortaleza')
    GOOGLE_CALENDAR_ICS_URL = os.getenv('GOOGLE_CALENDAR_ICS_URL', None)  # Se None, será construído
    CALENDAR_CACHE_TTL_MINUTES = int(os.getenv('CALENDAR_CACHE_TTL_MINUTES', '15'))
