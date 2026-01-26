from src.app import app
import os

if __name__ == '__main__':
    # Importar Waitress para o servidor de produção
    from waitress import serve
    
    # Configurar a aplicação para produção
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Iniciar servidor na porta 5000
    serve(app, host='127.0.0.1', port=5000, threads=4)
