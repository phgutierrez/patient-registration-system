from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import os
import signal

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
@login_required
def index():
    return render_template('index.html')

@main.route('/shutdown', methods=['POST'])
@login_required
def shutdown():
    """Rota para desligar o servidor"""
    try:
        # Enviar sinal de término para o processo principal
        os.kill(os.getpid(), signal.SIGTERM)
        return jsonify({'success': True, 'message': 'Servidor sendo encerrado...'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500