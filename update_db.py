from src.app import create_app, db
from src.models.patient import Patient
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Verificar se os campos existem
    inspector = db.inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('patient')]

    print("Campos existentes na tabela patient:")
    for col in columns:
        print(f"- {col}")

    # Adicionar campos se não existirem
    if 'endereco' not in columns:
        print("\nAdicionando campo 'endereco'...")
        db.session.execute(
            text('ALTER TABLE patient ADD COLUMN endereco VARCHAR(200)'))

    if 'estado' not in columns:
        print("\nAdicionando campo 'estado'...")
        db.session.execute(
            text('ALTER TABLE patient ADD COLUMN estado VARCHAR(2)'))

    db.session.commit()
    print("\nAtualização concluída!")
