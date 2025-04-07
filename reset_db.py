from src.app import app, db
from src.models.user import User
from src.models.patient import Patient
from src.models.surgery_request import SurgeryRequest
from datetime import datetime

def reset_database():
    """Recria o banco de dados com todas as tabelas atualizadas."""
    print("Recriando o banco de dados...")
    
    with app.app_context():
        # Apagar todas as tabelas existentes
        db.drop_all()
        print("✓ Tabelas removidas")
        
        # Criar todas as tabelas novamente com os modelos atualizados
        db.create_all()
        print("✓ Tabelas criadas")
        
        # Criar usuário administrador padrão
        admin = User(
            username='admin',
            password='admin123',
            role='administrador'
        )
        db.session.add(admin)
        db.session.commit()
        print("✓ Usuário admin criado")
        
        print("\n✅ Banco de dados inicializado com sucesso!")
        print("👤 Usuário admin criado (senha: admin123)")

if __name__ == "__main__":
    reset_database()