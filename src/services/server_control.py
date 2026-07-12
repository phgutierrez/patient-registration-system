from __future__ import annotations

import logging
import os
import threading
import time
from typing import Callable

logger = logging.getLogger(__name__)


class ServerController:
    """Thread-safe lifecycle controller for the local Waitress instance."""

    def __init__(self):
        self._lock = threading.RLock()
        self._server = None
        self._cleanup: Callable[[], None] | None = None
        self._state = 'stopped'
        self._origin = None
        self._stopped = threading.Event()
        self._allow_force_exit = False

    def register(self, server, cleanup: Callable[[], None] | None = None, *, allow_force_exit=False):
        with self._lock:
            self._server = server
            self._cleanup = cleanup
            self._state = 'running'
            self._origin = None
            self._allow_force_exit = bool(allow_force_exit)
            self._stopped.clear()
        logger.info('Controlador do servidor registrado.')

    def status(self) -> dict:
        with self._lock:
            return {'state': self._state, 'origin': self._origin}

    def request_shutdown(self, origin='unknown', *, delay=0.35, fallback_timeout=10) -> bool:
        with self._lock:
            if self._state != 'running' or self._server is None:
                return False
            self._state = 'stopping'
            self._origin = origin
            server = self._server
            cleanup = self._cleanup
            allow_force_exit = self._allow_force_exit
        logger.info('Encerramento solicitado (%s).', origin)

        def stop_server():
            time.sleep(max(0, delay))
            if cleanup:
                try:
                    cleanup()
                except Exception:
                    logger.exception('Falha na limpeza anterior ao encerramento.')
            try:
                server.close()
            except Exception:
                logger.exception('Falha ao fechar o listener Waitress.')
            try:
                server.task_dispatcher.shutdown(cancel_pending=False, timeout=5)
            except Exception:
                logger.exception('Falha ao aguardar tarefas do Waitress.')
            # Close keep-alive channels so the asyncore map can become empty
            # and server.run() can return naturally.
            for channel in list(getattr(server, '_map', {}).values()):
                try:
                    channel.close()
                except Exception:
                    logger.debug('Canal Waitress já estava fechado.', exc_info=True)

        threading.Thread(target=stop_server, name='server-shutdown', daemon=True).start()

        if allow_force_exit:
            def watchdog():
                if not self._stopped.wait(fallback_timeout):
                    logger.error('Waitress não encerrou em %ss; aplicando fallback do executável.', fallback_timeout)
                    os._exit(0)
            threading.Thread(target=watchdog, name='shutdown-watchdog', daemon=True).start()
        return True

    def mark_stopped(self):
        with self._lock:
            self._state = 'stopped'
            self._server = None
        self._stopped.set()
        logger.info('Servidor encerrado.')

    def reset_for_tests(self):
        with self._lock:
            self._server = None
            self._cleanup = None
            self._state = 'stopped'
            self._origin = None
            self._allow_force_exit = False
            self._stopped.set()


server_controller = ServerController()
