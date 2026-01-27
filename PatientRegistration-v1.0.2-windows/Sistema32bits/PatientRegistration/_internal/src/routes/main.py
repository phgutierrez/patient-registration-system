from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import os
import sys
import threading

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
        def shutdown_server():
            """Função para encerrar o servidor após responder à requisição"""
            import time
            time.sleep(1)  # Aguardar a resposta ser enviada
            
            # Tentar diferentes métodos de shutdown
            try:
                # Método 1: Usar sys.exit() em uma thread separada
                sys.exit(0)
            except:
                # Método 2: Forçar encerramento do processo
                os._exit(0)
        
        # Iniciar thread de shutdown
        threading.Thread(target=shutdown_server, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Servidor sendo encerrado...'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500