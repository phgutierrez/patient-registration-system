import sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.app import create_app, db
from src.models.user import User
from src.models.patient import Patient
from src.models.surgery_request import SurgeryRequest
from src.models.specialty import Specialty

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

        # Criar especialidades iniciais
        print("Criando especialidades iniciais...")
        now = datetime.utcnow()
        specialties_data = [
            {'slug': 'ortopedia', 'name': 'Ortopedia'},
            {'slug': 'cirurgia_pediatrica', 'name': 'Cirurgia Pediátrica'},
        ]
        specialties = []
        for spec_data in specialties_data:
            spec = Specialty(
                slug=spec_data['slug'],
                name=spec_data['name'],
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.session.add(spec)
            specialties.append(spec)
        db.session.flush()  # gera IDs antes de criar settings

        # Criar settings para cada especialidade
        try:
            from src.models.specialty import SpecialtySettings
            forms_url_ortopedia = 'https://docs.google.com/forms/d/e/1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg/viewform'
            for i, spec in enumerate(specialties):
                setting = SpecialtySettings(
                    specialty_id=spec.id,
                    forms_url=forms_url_ortopedia if i == 0 else '',
                    agenda_url='',
                    created_at=now,
                    updated_at=now,
                )
                db.session.add(setting)
        except Exception as e:
            print(f"  [AVISO] Não foi possível criar specialty_settings: {e}")
        
        # Criar usuários iniciais
        print("Criando usuários iniciais...")
        
        users_data = [
            {'username': 'pedro', 'full_name': 'Pedro Freitas', 'cns': None, 'crm': None},
            {'username': 'andre', 'full_name': 'André Cristiano', 'cns': None, 'crm': None},
            {'username': 'brauner', 'full_name': 'Brauner Cavalcanti', 'cns': None, 'crm': None},
            {'username': 'savio', 'full_name': 'Sávio Bruno', 'cns': None, 'crm': None},
            {'username': 'laecio', 'full_name': 'Laecio Damaceno', 'cns': None, 'crm': None},
        ]
        
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                password='123456',  # Senha padrão
                full_name=user_data['full_name'],
                cns=user_data['cns'],
                crm=user_data['crm'],
                specialty_id=specialties[0].id,  # Ortopedia por padrão
                role='solicitante'
            )
            db.session.add(user)
        
        db.session.commit()
        
        print("""
✅ Banco de dados inicializado com sucesso!

Especialidades criadas:
- Ortopedia
- Cirurgia Pediátrica

Usuários criados:
- Pedro Freitas
- André Cristiano
- Brauner Cavalcanti
- Sávio Bruno
- Laecio Damaceno
Senha padrão: 123456
        """)

if __name__ == "__main__":
    init_db()