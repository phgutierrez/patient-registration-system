from flask import Flask, redirect, url_for, render_template
from src.config import Config
from src.extensions import db, login_manager, csrf, migrate
import logging
import traceback
import os

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    # Verificar se há um instance_path personalizado
    instance_path = os.environ.get('INSTANCE_PATH')
    
    if instance_path:
        app = Flask(__name__, instance_path=instance_path)
    else:
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

    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for('auth.select_user'))

    # Handler de erros global
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f'Erro não tratado: {error}', exc_info=True)
        error_trace = traceback.format_exc()
        logger.error(f'Traceback:\n{error_trace}')
        
        # Em desenvolvimento, mostrar erro detalhado
        if app.debug:
            return f'<h1>Erro</h1><pre>{error_trace}</pre>', 500
        
        # Em produção, mensagem genérica
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Erro - Patient Registration System</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    .error { background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 5px; }
                    h1 { color: #c00; }
                    .details { background: #f5f5f5; padding: 10px; margin-top: 20px; border-radius: 3px; }
                    code { background: #eee; padding: 2px 5px; border-radius: 3px; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>⚠️ Erro no Servidor</h1>
                    <p>Ocorreu um erro ao processar sua solicitação.</p>
                    <div class="details">
                        <strong>Detalhes técnicos:</strong><br>
                        <code>{{ error }}</code>
                    </div>
                    <p style="margin-top: 20px;">
                        <a href="{{ url_for('auth.select_user') }}" style="color: #0066cc;">← Voltar ao início</a>
                    </p>
                </div>
            </body>
            </html>
        ''', error=str(error)), 500

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


def render_template_string(template, **context):
    """Helper para renderizar template string"""
    from flask import render_template_string as rts, url_for
    context['url_for'] = url_for
    return rts(template, **context)


app = create_app()
