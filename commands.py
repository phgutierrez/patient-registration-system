import click
from flask.cli import with_appcontext
from src.app import db, create_app
from src.models.user import User

app = create_app()

@click.group()
def cli():
    """Comandos de gerenciamento do sistema"""
    pass

@cli.command()
@with_appcontext
def init_db():
    """Inicializa o banco de dados"""
    with app.app_context():
        # Cria todas as tabelas
        db.create_all()
        
        # Cria usuário admin se não existir
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password='admin123',
                role='administrador'
            )
            db.session.add(admin)
            db.session.commit()
            click.echo('Usuário admin criado com sucesso!')
        
        click.echo('Banco de dados inicializado!')

if __name__ == '__main__':
    cli()