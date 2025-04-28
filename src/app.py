from flask import Flask
from src.config import Config
from src.extensions import db, login_manager, csrf, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Configuração do login_manager
    from src.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar blueprints
    from src.routes.auth import auth
    from src.routes.main import main
    from src.routes.patients import patients
    from src.routes.surgery import surgery

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(patients)
    app.register_blueprint(surgery)

    return app


app = create_app()
