import tempfile
import unittest
from pathlib import Path

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty
from src.models.user import User


class AuthenticationSessionTests(unittest.TestCase):
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
            DESKTOP_MODE = True
            SERVER_BIND_HOST = '127.0.0.1'

        self.app = create_app(TestConfig)
        with self.app.app_context():
            db.create_all()
            specialty = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            db.session.add(specialty)
            db.session.flush()
            user = User(
                username='medico', password='012345', full_name='Médico Teste',
                role='solicitante', specialty_id=specialty.id,
            )
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def _authenticate(self, client):
        with client.session_transaction() as session:
            session['specialty_slug'] = 'ortopedia'
        response = client.post('/', data={'action': 'select_user', 'username': 'medico'})
        self.assertEqual(302, response.status_code)
        response = client.post('/', data={'action': 'authenticate', 'password': '012345'})
        self.assertEqual(302, response.status_code)

    def test_logout_preserves_orthopedics_and_requires_new_selection(self):
        client = self.app.test_client()
        self._authenticate(client)
        response = client.get('/logout')
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.location.endswith('/'))
        with client.session_transaction() as session:
            self.assertEqual('ortopedia', session.get('specialty_slug'))
            self.assertNotIn('_user_id', session)
            self.assertNotIn('pending_user_id', session)
            self.assertNotIn('desktop_runtime_id', session)

        selection = client.get('/')
        self.assertEqual(200, selection.status_code)
        self.assertIn('Médico Teste'.encode('utf-8'), selection.data)

    def test_old_desktop_cookie_is_invalidated_after_restart(self):
        client = self.app.test_client()
        with client.session_transaction() as session:
            session['_user_id'] = str(self.user_id)
            session['_fresh'] = True
            session['pending_user_id'] = self.user_id
            session['specialty_slug'] = 'ortopedia'
            session['desktop_runtime_id'] = 'execucao-anterior'

        response = client.get('/patients/')
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.location.endswith('/'))
        with client.session_transaction() as session:
            self.assertEqual('ortopedia', session.get('specialty_slug'))
            self.assertNotIn('_user_id', session)
            self.assertNotIn('pending_user_id', session)

    def test_successful_login_is_bound_to_current_runtime(self):
        client = self.app.test_client()
        self._authenticate(client)
        with client.session_transaction() as session:
            self.assertEqual(
                self.app.config['DESKTOP_RUNTIME_ID'],
                session.get('desktop_runtime_id'),
            )
            self.assertEqual(str(self.user_id), session.get('_user_id'))


if __name__ == '__main__':
    unittest.main()
