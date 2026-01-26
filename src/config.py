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