from src.app import app
from src.extensions import db
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar banco de dados
def initialize_database():
    """Cria as tabelas do banco de dados se não existirem e adiciona usuário padrão"""
    try:
        with app.app_context():
            # Verificar se o banco de dados precisa ser inicializado
            from pathlib import Path
            db_path = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///patient_registration.db')
            db_file = db_path.replace('sqlite:///', '').replace('sqlite:////','')
            
            logger.info(f"Banco de dados: {db_file}")
            
            # Criar as tabelas se não existirem
            db.create_all()
            logger.info("Banco de dados inicializado com sucesso")
            
            # Criar usuário padrão se não existir nenhum usuário
            try:
                from src.models.user import User
                if User.query.first() is None:
                    # Criar usuário padrão para teste
                    default_user = User(
                        username='admin',
                        email='admin@example.com',
                        full_name='Administrador'
                    )
                    default_user.set_password('admin123')
                    db.session.add(default_user)
                    db.session.commit()
                    logger.info("Usuário padrão 'admin' criado com sucesso (senha: admin123)")
            except Exception as user_error:
                logger.warning(f"Não foi possível criar usuário padrão: {user_error}")
                
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")

if __name__ == '__main__':
    # Inicializar banco de dados
    initialize_database()
    
    # Importar Waitress para o servidor de produção
    from waitress import serve
    
    # Configurar a aplicação para produção
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    
    logger.info("Iniciando servidor Waitress na porta 5000...")
    # Iniciar servidor na porta 5000
    serve(app, host='127.0.0.1', port=5000, threads=4)
