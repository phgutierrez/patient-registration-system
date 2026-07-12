import threading
import time
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Global lifecycle state
state = {
    'sessions': {},  # session_id -> last_heartbeat (datetime)
    'had_sessions': False,
    'empty_since': None,
}
_monitor_started = False
_state_lock = threading.RLock()


def generate_session_id() -> str:
    return str(uuid.uuid4())


def touch_session(session_id: str):
    """Registra/atualiza o heartbeat da sessão"""
    with _state_lock:
        state['sessions'][session_id] = datetime.utcnow()
        state['had_sessions'] = True
        state['empty_since'] = None


def remove_session(session_id: str):
    with _state_lock:
        state['sessions'].pop(session_id, None)
        if state['had_sessions'] and not state['sessions'] and state['empty_since'] is None:
            state['empty_since'] = datetime.utcnow()


def expire_stale_sessions(now: datetime, heartbeat_timeout: int) -> list[str]:
    with _state_lock:
        stale = [session_id for session_id, last in state['sessions'].items()
                 if (now - last).total_seconds() > heartbeat_timeout]
        for session_id in stale:
            state['sessions'].pop(session_id, None)
        if stale and state['had_sessions'] and not state['sessions'] and state['empty_since'] is None:
            state['empty_since'] = now
        return stale


def should_shutdown(now: datetime, grace_seconds: int) -> bool:
    with _state_lock:
        return bool(
            state['had_sessions'] and not state['sessions']
            and state['empty_since'] is not None
            and (now - state['empty_since']).total_seconds() >= grace_seconds
        )


def start_monitor(app):
    """Inicia thread que monitora heartbeat e encerra o servidor quando necessário.

    Regras:
    - Só ativa se DESKTOP_MODE == True
    - Só fecha se SERVER_BIND_HOST for 127.0.0.1 ou localhost
    - Usa LIFECYCLE_TIMEOUT_SECONDS para decidir timeout
    - Desabilitado automaticamente no modo network (0.0.0.0)
    """
    global _monitor_started
    if _monitor_started:
        return
    _monitor_started = True

    def monitor():
        # Check initial config to determine if monitor should run
        with app.app_context():
            desktop_mode = app.config.get('DESKTOP_MODE', False)
            bind_host = app.config.get('SERVER_BIND_HOST', '127.0.0.1')
            
            if not desktop_mode:
                logger.info("Lifecycle monitor disabled (DESKTOP_MODE=false)")
                return
                
            if str(bind_host) not in ('127.0.0.1', 'localhost'):
                logger.info(f"Lifecycle monitor disabled (network mode, bind_host={bind_host})")
                return
                
            logger.info("Lifecycle monitor iniciado (desktop mode)")
            
        while True:
            try:
                time.sleep(1)
                with app.app_context():
                    desktop_mode = app.config.get('DESKTOP_MODE', False)
                    bind_host = app.config.get('SERVER_BIND_HOST', '127.0.0.1')
                    timeout_seconds = int(app.config.get('LIFECYCLE_TIMEOUT_SECONDS', 30))
                    grace_seconds = int(app.config.get('LIFECYCLE_SHUTDOWN_GRACE_SECONDS', 15))

                    if not desktop_mode:
                        continue

                    if str(bind_host) not in ('127.0.0.1', 'localhost'):
                        continue

                    now = datetime.utcnow()
                    stale_sessions = expire_stale_sessions(now, timeout_seconds)
                    if stale_sessions:
                        logger.info('%d sessão(ões) local(is) expiraram.', len(stale_sessions))
                    if should_shutdown(now, grace_seconds):
                        from src.services.server_control import server_controller
                        if server_controller.request_shutdown('last-browser-closed'):
                            break
            except Exception:
                logger.exception("Erro no monitor de lifecycle")

    t = threading.Thread(target=monitor, daemon=True)
    t.start()
