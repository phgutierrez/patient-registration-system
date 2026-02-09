#!/usr/bin/env python3
"""
Script para criar todas as tabelas diretamente via SQLAlchemy
Pula o sistema de migrações problemático
"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.extensions import db

def create_tables():
    """Criar todas as tabelas definidas nos modelos"""
    app = create_app()
    
    with app.app_context():
        # Remover banco existente se necessário
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if db_path and os.path.exists(db_path):
            os.remove(db_path)
            print(f"Banco removido: {db_path}")
        
        # Criar todas as tabelas
        db.create_all()
        print("Todas as tabelas criadas com sucesso!")
        
        # Verificar as tabelas criadas
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tabelas criadas: {tables}")
        
        # Verificar especificamente a tabela calendar_cache
        if 'calendar_cache' in tables:
            columns = inspector.get_columns('calendar_cache')
            column_names = [col['name'] for col in columns]
            print(f"Colunas da calendar_cache: {column_names}")
            
            if 'etag' in column_names and 'last_modified' in column_names:
                print("✓ Colunas ETag e Last-Modified foram criadas corretamente!")
            else:
                print("✗ Colunas ETag/Last-Modified não foram encontradas")

if __name__ == '__main__':
    create_tables()