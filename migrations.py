from src.app import app
from flask_migrate import Migrate
from src.app import db

migrate = Migrate(app, db)