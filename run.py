from src.app import app
import signal
import sys
import logging
import atexit

def signal_handler(sig, frame):
    print('\nDesligando o servidor...')
    logging.shutdown()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(logging.shutdown)
    app.run(debug=True, host='0.0.0.0', port=5000)
