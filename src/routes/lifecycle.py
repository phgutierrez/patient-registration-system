from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from src.services import lifecycle as lifecycle_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('lifecycle', __name__)


@bp.route('/lifecycle/heartbeat', methods=['POST'])
@login_required
def heartbeat():
    data = request.get_json() or {}
    session = data.get('session')
    if not session:
        return jsonify({'error': 'session required'}), 400

    lifecycle_service.touch_session(session)
    return jsonify({'ok': True}), 200


@bp.route('/lifecycle/shutdown', methods=['POST'])
@login_required
def shutdown():
    data = request.get_json() or {}
    session = data.get('session')
    if session:
        lifecycle_service.remove_session(session)

    # Try to perform graceful shutdown (main.shutdown route exists and will attempt sys.exit)
    try:
        # Respond quickly; actual shutdown handled by monitor or main.shutdown when invoked manually
        return jsonify({'ok': True}), 200
    except Exception as e:
        logger.exception('Erro ao solicitar shutdown')
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/lifecycle/session', methods=['GET'])
@login_required
def session_info():
    # Retorna listagem simples de sessões (sem dados sensíveis)
    sessions = list(lifecycle_service.state.get('sessions', {}).keys())
    return jsonify({'sessions': sessions, 'count': len(sessions)}), 200
