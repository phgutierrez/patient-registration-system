from src.app import create_app

# WSGI entrypoint for production servers like Waitress
application = create_app()
app = application  # Compatibility alias

if __name__ == '__main__':
    # Only for local development - production should use waitress-serve
    app.run(debug=False, host='127.0.0.1', port=5000)