import threading
import time
import unittest
from types import SimpleNamespace
from flask import Flask

from src.services.server_control import ServerController, server_controller
from src.routes.main import main


class FakeDispatcher:
    def __init__(self):
        self.calls = []

    def shutdown(self, **kwargs):
        self.calls.append(kwargs)


class FakeChannel:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeServer:
    def __init__(self):
        self.closed = False
        self.task_dispatcher = FakeDispatcher()
        self.channel = FakeChannel()
        self._map = {'channel': self.channel}

    def close(self):
        self.closed = True


class ServerControllerTests(unittest.TestCase):
    def test_shutdown_is_idempotent_and_cleans_up(self):
        controller = ServerController()
        server = FakeServer()
        cleaned = threading.Event()
        controller.register(server, cleaned.set)
        self.assertTrue(controller.request_shutdown('test', delay=0))
        self.assertFalse(controller.request_shutdown('duplicate', delay=0))
        deadline = time.time() + 2
        while not server.closed and time.time() < deadline:
            time.sleep(0.01)
        self.assertTrue(cleaned.is_set())
        self.assertTrue(server.closed)
        self.assertTrue(server.channel.closed)
        self.assertEqual([{'cancel_pending': False, 'timeout': 5}], server.task_dispatcher.calls)
        self.assertEqual('stopping', controller.status()['state'])
        controller.mark_stopped()
        self.assertEqual('stopped', controller.status()['state'])

    def test_unregistered_controller_refuses_shutdown(self):
        controller = ServerController()
        self.assertFalse(controller.request_shutdown('test', delay=0))


class ShutdownRouteTests(unittest.TestCase):
    def setUp(self):
        server_controller.reset_for_tests()
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY='test', DESKTOP_MODE=True)
        self.app.register_blueprint(main)

    def tearDown(self):
        server_controller.reset_for_tests()

    def test_local_shutdown_works_without_login(self):
        server_controller.register(FakeServer())
        client = self.app.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = '12'
            session['pending_user_id'] = 12
            session['specialty_slug'] = 'ortopedia'
        response = client.post('/shutdown', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(202, response.status_code)
        self.assertTrue(response.get_json()['success'])
        with client.session_transaction() as session:
            self.assertEqual('ortopedia', session.get('specialty_slug'))
            self.assertNotIn('_user_id', session)
            self.assertNotIn('pending_user_id', session)

    def test_remote_shutdown_is_forbidden(self):
        server_controller.register(FakeServer())
        response = self.app.test_client().post('/shutdown', environ_base={'REMOTE_ADDR': '192.168.1.50'})
        self.assertEqual(403, response.status_code)

    def test_network_mode_shutdown_is_forbidden(self):
        self.app.config['DESKTOP_MODE'] = False
        server_controller.register(FakeServer())
        response = self.app.test_client().post('/shutdown', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(403, response.status_code)


if __name__ == '__main__':
    unittest.main()
