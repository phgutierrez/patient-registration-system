from flask import Flask, redirect, url_for, render_template, request
from flask_login import current_user
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException
from src.config import Config
from src.extensions import db, login_manager, csrf, migrate, limiter
from src.runtime_security import ensure_security_schema, migrate_legacy_pdf_storage, bootstrap_admin_if_configured
import logging
import traceback
import os

logger = logging.getLogger(__name__)


def _request_is_secure() -> bool:
    forwarded_proto = (request.headers.get('X-Forwarded-Proto') or '').strip().lower()
    forwarded_ssl = (request.headers.get('X-Forwarded-Ssl') or '').strip().lower()
    return request.is_secure or forwarded_proto == 'https' or forwarded_ssl == 'on'


def _append_csp_report_uri(policy: str, report_uri: str) -> str:
    normalized_policy = (policy or '').strip().rstrip(';')
    normalized_report_uri = (report_uri or '').strip()
    if not normalized_policy or not normalized_report_uri:
        return normalized_policy
    return f'{normalized_policy}; report-uri {normalized_report_uri}'


def create_app(config_class=Config):
    # Verificar se há um instance_path personalizado
    instance_path = os.environ.get('INSTANCE_PATH')
    
    if instance_path:
        app = Flask(__name__, instance_path=instance_path)
    else:
        app = Flask(__name__)
    
    app.config.from_object(config_class)
    migrate_legacy_pdf_storage(app)
    ensure_security_schema(app)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    bootstrap_admin_if_configured(app)

    # Configuração do login_manager
    from src.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for('auth.select_user'))

    @app.before_request
    def enforce_password_change():
        if not current_user.is_authenticated:
            return None
        if not getattr(current_user, 'must_change_password', False):
            return None

        allowed_endpoints = {
            'auth.change_password',
            'auth.logout',
            'auth.select_user',
            'auth.set_specialty_pre_login',
            'static',
        }
        if request.endpoint in allowed_endpoints:
            return None
        return redirect(url_for('auth.change_password'))

    @app.errorhandler(403)
    def handle_forbidden(error):
        message = getattr(error, 'description', 'Você não tem permissão para acessar este recurso.')
        if request.accept_mimetypes.best == 'application/json' or request.path.startswith('/patients/api/') or request.path.startswith('/surgery_requests/'):
            return {'error': message}, 403
        return render_template('error.html', title='Acesso negado', message=message), 403

    @app.errorhandler(429)
    def handle_rate_limit(error):
        message = 'Muitas tentativas em sequência. Aguarde um instante e tente novamente.'
        if request.accept_mimetypes.best == 'application/json' or request.path.startswith('/patients/api/') or request.path.startswith('/surgery_requests/'):
            return {'error': message}, 429
        return render_template('error.html', title='Limite atingido', message=message), 429

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        message = 'Sua sessão de segurança expirou ou a requisição é inválida. Recarregue a página e tente novamente.'
        if request.accept_mimetypes.best == 'application/json' or request.path.startswith('/patients/api/') or request.path.startswith('/surgery_requests/'):
            return {'error': message}, 400
        return render_template('error.html', title='Requisição inválida', message=message), 400

    @app.after_request
    def apply_security_headers(response):
        if not app.config.get('SECURITY_HEADERS_ENABLED', True):
            return response

        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.headers.setdefault('Cross-Origin-Resource-Policy', 'same-origin')

        csp_policy = _append_csp_report_uri(
            app.config.get('SECURITY_CSP_REPORT_ONLY_POLICY', ''),
            app.config.get('SECURITY_CSP_REPORT_URI', ''),
        )
        if app.config.get('SECURITY_CSP_REPORT_ONLY', True) and csp_policy:
            response.headers.setdefault('Content-Security-Policy-Report-Only', csp_policy)

        is_authenticated_response = current_user.is_authenticated and request.endpoint != 'static'
        is_sensitive_json = (
            response.mimetype == 'application/json'
            and (
                request.path.startswith('/patients/')
                or request.path.startswith('/surgery_requests/')
                or request.path.startswith('/agenda')
            )
        )
        is_protected_pdf = response.mimetype == 'application/pdf'
        if is_authenticated_response or is_sensitive_json or is_protected_pdf:
            response.headers['Cache-Control'] = 'no-store'

        if app.config.get('SECURITY_HSTS_ENABLED', False) and _request_is_secure():
            hsts_value = f"max-age={int(app.config.get('SECURITY_HSTS_MAX_AGE_SECONDS', 31536000))}"
            if app.config.get('SECURITY_HSTS_INCLUDE_SUBDOMAINS', True):
                hsts_value = f'{hsts_value}; includeSubDomains'
            if app.config.get('SECURITY_HSTS_PRELOAD', False):
                hsts_value = f'{hsts_value}; preload'
            response.headers.setdefault('Strict-Transport-Security', hsts_value)

        return response

    # Handler de erros global
    @app.errorhandler(Exception)
    def handle_error(error):
        if isinstance(error, HTTPException):
            return error
        logger.error(f'Erro não tratado: {error}', exc_info=True)
        error_trace = traceback.format_exc()
        logger.error(f'Traceback:\n{error_trace}')
        
        # Em desenvolvimento, mostrar erro detalhado
        if app.debug:
            return f'<h1>Erro</h1><pre>{error_trace}</pre>', 500
        
        # Em produção, mensagem genérica
        return render_template('error.html', title='Erro no servidor',
                               message='Ocorreu um erro ao processar sua solicitação. Tente novamente em instantes.'), 500

    # Registrar blueprints
    from src.routes.auth import auth
    from src.routes.main import main
    from src.routes.patients import patients
    from src.routes.surgery import surgery
    from src.routes.lifecycle import bp as lifecycle_bp
    from src.routes.specialty_settings import specialty_settings_bp

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(patients)
    app.register_blueprint(surgery)
    app.register_blueprint(lifecycle_bp)
    app.register_blueprint(specialty_settings_bp)

    # Context processor: especialidade ativa disponível em todos os templates
    from src.services.specialty_service import specialty_context

    @app.context_processor
    def inject_specialty():
        try:
            return specialty_context()
        except Exception:
            return {'active_specialty': 'ortopedia', 'active_specialty_name': 'Ortopedia', 'active_specialty_obj': None}

    # Inicializar monitor de lifecycle (se o módulo estiver disponível)
    try:
        from src.services.lifecycle import start_monitor
        start_monitor(app)
    except Exception:
        logger.exception('Não foi possível iniciar o monitor de lifecycle')

    return app
app = create_app()
