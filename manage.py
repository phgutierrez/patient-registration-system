import os
from flask_migrate import Migrate, current, init, migrate, upgrade
from src.app import app, db
from src.models.user import User
from src.models.patient import Patient
from src.models.surgery_request import SurgeryRequest

# Configurar a extensão de migração
migrate_instance = Migrate(app, db)

# Criar diretório de migrações se não existir
if not os.path.exists('migrations'):
    print("Criando repositório de migrações...")
    directory = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'migrations')
    init(directory=directory)

if __name__ == '__main__':
    import sys

    if len(sys.argv) <= 1:
        print("Uso: python manage.py [comando]")
        print("Comandos disponíveis:")
        print("  init_db     - Inicializar banco de dados")
        print("  migrate     - Criar migração")
        print("  upgrade     - Aplicar migrações")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init_db':
        # Inicializar banco de dados do zero
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Criar usuário admin
            admin = User(
                username='admin',
                password='admin123',
                role='administrador'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Banco de dados inicializado")
            print("👤 Usuário admin criado com senha: admin123")

    elif command == 'migrate':
        # Criar nova migração
        message = sys.argv[2] if len(sys.argv) > 2 else "Migração automática"
        directory = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'migrations')
        # Executar dentro do contexto da aplicação
        with app.app_context():
            migrate(directory=directory, message=message)
        print(f"✅ Migração criada: {message}")

    elif command == 'upgrade':
        # Aplicar migrações
        directory = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'migrations')
        # Executar dentro do contexto da aplicação
        with app.app_context():
            upgrade(directory=directory)
        print("✅ Migrações aplicadas com sucesso")

    else:
        print(f"Comando desconhecido: {command}")
        print("Comandos disponíveis: init_db, migrate, upgrade")
