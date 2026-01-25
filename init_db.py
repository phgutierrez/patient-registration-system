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
        
        # Criar usuários iniciais
        print("Criando usuários iniciais...")
        
        users_data = [
            {'username': 'pedro', 'full_name': 'Pedro Silva', 'cns': None, 'crm': None},
            {'username': 'andre', 'full_name': 'André Costa', 'cns': None, 'crm': None},
            {'username': 'brauner', 'full_name': 'Brauner Santos', 'cns': None, 'crm': None},
            {'username': 'savio', 'full_name': 'Sávio Oliveira', 'cns': None, 'crm': None},
            {'username': 'laecio', 'full_name': 'Laecio Ferreira', 'cns': None, 'crm': None},
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
        
        db.session.commit()
        
        print("""
✅ Banco de dados inicializado com sucesso!

Usuários criados:
- Pedro Silva
- André Costa
- Brauner Santos
- Sávio Oliveira
- Laecio Ferreira

Senha padrão: 123456
        """)

if __name__ == "__main__":
    init_db()