import tempfile
import unittest
from pathlib import Path

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty
from src.models.user import User


class FirstAdminTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        database = Path(self.tempdir.name) / 'test.db'

        class TestConfig:
            TESTING = True
            SECRET_KEY = 'test-secret-key-that-is-long-enough'
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{database}'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = False
            RATELIMIT_ENABLED = False
            PROTECTED_PDF_DIR = Path(self.tempdir.name) / 'pdfs'
            ADMIN_BOOTSTRAP_USERNAME = ''
            ADMIN_BOOTSTRAP_PASSWORD = ''
            SECURITY_HEADERS_ENABLED = False
            DESKTOP_MODE = False
            SERVER_BIND_HOST = '127.0.0.1'

        self.app = create_app(TestConfig)
        with self.app.app_context():
            db.create_all()
            db.session.add(Specialty(slug='ortopedia', name='Ortopedia', is_active=True))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def _select_orthopedics(self, client):
        with client.session_transaction() as session:
            session['specialty_slug'] = 'ortopedia'

    def test_local_empty_install_redirects_to_first_admin(self):
        client = self.app.test_client()
        self._select_orthopedics(client)
        response = client.get('/', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(302, response.status_code)
        self.assertIn('/primeiro-acesso', response.location)

    def test_remote_client_cannot_open_wizard(self):
        client = self.app.test_client()
        response = client.get('/primeiro-acesso', environ_base={'REMOTE_ADDR': '192.168.1.25'})
        self.assertEqual(403, response.status_code)

    def test_first_admin_is_created_once(self):
        client = self.app.test_client()
        response = client.post(
            '/primeiro-acesso',
            data={
                'full_name': 'Administrador Local', 'username': 'admin.local',
                'password': '012345', 'confirm_password': '012345',
            },
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(302, response.status_code)
        with self.app.app_context():
            user = User.query.one()
            self.assertTrue(user.is_admin)
            self.assertEqual('ortopedia', user.specialty.slug)
            self.assertFalse(user.must_change_password)

        second = client.get('/primeiro-acesso', environ_base={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(302, second.status_code)
        with self.app.app_context():
            self.assertEqual(1, User.query.count())


if __name__ == '__main__':
    unittest.main()
