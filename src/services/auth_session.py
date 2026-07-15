"""Operações centralizadas para o estado de autenticação da sessão."""
from flask import current_app, session
from flask_login import current_user, logout_user


ORTHOPEDICS_SLUG = 'ortopedia'
RUNTIME_SESSION_KEY = 'desktop_runtime_id'


def clear_authentication_session(*, preserve_specialty: bool = True) -> None:
    """Remove usuário e seleção pendente, preservando apenas Ortopedia."""
    # Alguns testes e utilitários registram a rota sem inicializar Flask-Login.
    if hasattr(current_app, 'login_manager') and current_user.is_authenticated:
        logout_user()
    session.clear()
    if preserve_specialty:
        session['specialty_slug'] = ORTHOPEDICS_SLUG
    session.modified = True


def bind_session_to_current_runtime() -> None:
    """Vincula a seleção/login à execução atual do servidor desktop."""
    if current_app.config.get('DESKTOP_MODE', False):
        session[RUNTIME_SESSION_KEY] = current_app.config['DESKTOP_RUNTIME_ID']
        session.modified = True


def has_stale_desktop_authentication() -> bool:
    """Informa se usuário autenticado/pendente pertence a outra execução local."""
    if not current_app.config.get('DESKTOP_MODE', False):
        return False
    has_authentication_state = bool(session.get('_user_id') or session.get('pending_user_id'))
    if not has_authentication_state:
        return False
    return session.get(RUNTIME_SESSION_KEY) != current_app.config.get('DESKTOP_RUNTIME_ID')
