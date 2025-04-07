from flask_migrate import Migrate, MigrateCommand
from flask.cli import FlaskGroup
from src.app import app, db

migrate = Migrate(app, db)

cli = FlaskGroup(app)

if __name__ == '__main__':
    cli()