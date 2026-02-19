import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.app import create_app, db
from src.models.user import User
from src.models.patient import Patient
from src.models.surgery_request import SurgeryRequest

def init_db():
    """Inicializar o banco de dados com todos os modelos atuais"""
    print("Inicializando banco de dados...")
    app = create_app()
    
    with app.app_context():
        # Remover todas as tabelas existentes
        print("Removendo tabelas existentes...")
        db.drop_all()
        
        # Criar todas as tabelas conforme os modelos atuais
        print("Criando novas tabelas...")
        db.create_all()
        
        # Criar usuário admin
        print("Criando usuário administrador...")
        
        # Corrigido: fornecendo o parâmetro 'password' necessário
        admin = User(
            username='admin',
            password='admin123',
            full_name='Administrador',
            role='administrador'
        )
        # Não é necessário chamar set_password() aqui, pois estamos passando a senha no construtor
        # Se a classe User estiver configurada para realizar o hash da senha no construtor
        
        db.session.add(admin)
        db.session.commit()
        
        print("""
✅ Banco de dados inicializado com sucesso!

Informações do usuário administrador:
- Username: admin
- Senha: admin123
        """)

if __name__ == "__main__":
    init_db()