import threading
import time
import uuid
from datetime import datetime, timedelta
from flask import current_app
import logging

logger = logging.getLogger(__name__)

# Global lifecycle state
state = {
    'sessions': {},  # session_id -> last_heartbeat (datetime)
}


def generate_session_id() -> str:
    return str(uuid.uuid4())


def touch_session(session_id: str):
    """Registra/atualiza o heartbeat da sessão"""
    state['sessions'][session_id] = datetime.utcnow()
    logger.debug(f"Heartbeat registered for session {session_id}")


def remove_session(session_id: str):
    if session_id in state['sessions']:
        del state['sessions'][session_id]


def start_monitor(app):
    """Inicia thread que monitora heartbeat e encerra o servidor quando necessário.

    Regras:
    - Só ativa se DESKTOP_MODE == True
    - Só fecha se SERVER_BIND_HOST for 127.0.0.1 ou localhost
    - Usa LIFECYCLE_TIMEOUT_SECONDS para decidir timeout
    """

    def monitor():
        logger.info("Lifecycle monitor iniciado")
        while True:
            try:
                time.sleep(5)
                with app.app_context():
                    desktop_mode = app.config.get('DESKTOP_MODE', False)
                    bind_host = app.config.get('SERVER_BIND_HOST', '127.0.0.1')
                    timeout_seconds = int(app.config.get('LIFECYCLE_TIMEOUT_SECONDS', 30))

                    if not desktop_mode:
                        continue

                    if str(bind_host) not in ('127.0.0.1', 'localhost'):
                        continue

                    now = datetime.utcnow()
                    # check all sessions
                    stale_sessions = []
                    for sess, last in list(state['sessions'].items()):
                        if (now - last).total_seconds() > timeout_seconds:
                            stale_sessions.append(sess)

                    if stale_sessions:
                        logger.info(f"Sessões sem heartbeat: {stale_sessions}. Iniciando shutdown gracioso...")
                        # Tentar shutdown gracioso via endpoint main.shutdown (se disponível)
                        try:
                            # Preferir encerrar pela própria aplicação
                            def do_shutdown():
                                import sys
                                logger.info("Executando shutdown gracioso do processo")
                                try:
                                    sys.exit(0)
                                except SystemExit:
                                    # fallback
                                    import os
                                    os._exit(0)

                            threading.Thread(target=do_shutdown, daemon=True).start()
                        except Exception as e:
                            logger.exception("Falha ao tentar shutdown gracioso: %s", e)
                            try:
                                import os
                                os._exit(0)
                            except Exception:
                                pass
                        break
            except Exception:
                logger.exception("Erro no monitor de lifecycle")

    t = threading.Thread(target=monitor, daemon=True)
    t.start()
