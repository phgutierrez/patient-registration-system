import click
from flask.cli import with_appcontext
from flask_migrate import Migrate
from src.app import create_app, db

app = create_app()
migrate = Migrate(app, db)

@click.group()
def cli():
    """Comandos de gerenciamento do sistema"""
    pass

@cli.command()
@with_appcontext
def init_db():
    """Inicializa o banco de dados"""
    db.create_all()
    click.echo('Banco de dados inicializado.')

if __name__ == '__main__':
    cli()