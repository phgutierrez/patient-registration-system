import tempfile
import unittest
from pathlib import Path

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty
from src.models.user import User


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        database = Path(self.tempdir.name) / 'profile.db'

        class TestConfig:
            TESTING = True
            SECRET_KEY = 'profile-test-secret-key'
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{database}'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = False
            RATELIMIT_ENABLED = False
            PROTECTED_PDF_DIR = Path(self.tempdir.name) / 'pdfs'
            ADMIN_BOOTSTRAP_USERNAME = ''
            ADMIN_BOOTSTRAP_PASSWORD = ''
            SECURITY_HEADERS_ENABLED = False
            DESKTOP_MODE = False

        self.app = create_app(TestConfig)
        with self.app.app_context():
            db.create_all()
            specialty = Specialty(
                slug='ortopedia', name='Ortopedia', is_active=True
            )
            db.session.add(specialty)
            db.session.flush()
            user = User(
                username='medico',
                password='senha-legada-maior',
                full_name='Médico Antigo',
                role='solicitante',
                specialty_id=specialty.id,
            )
            other = User(
                username='outro',
                password='654321',
                full_name='Outro Médico',
                role='solicitante',
                specialty_id=specialty.id,
                cns='123456789012345',
                crm='CRM EXISTENTE',
            )
            db.session.add_all([user, other])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def _login(self, client):
        with client.session_transaction() as session:
            session['specialty_slug'] = 'ortopedia'
        client.post('/', data={'action': 'select_user', 'username': 'medico'})
        response = client.post(
            '/',
            data={
                'action': 'authenticate',
                'password': 'senha-legada-maior',
            },
        )
        self.assertEqual(302, response.status_code)

    def test_user_updates_name_cns_and_crm_with_legacy_password(self):
        client = self.app.test_client()
        self._login(client)
        response = client.post('/perfil', data={
            'action': 'update_profile',
            'current_pin': 'senha-legada-maior',
            'full_name': 'Dra. Maria Atualizada',
            'cns': '987654321098765',
            'crm': ' crm 123 / ce ',
        })
        self.assertEqual(302, response.status_code)
        with self.app.app_context():
            user = User.query.filter_by(username='medico').one()
            self.assertEqual('Dra. Maria Atualizada', user.full_name)
            self.assertEqual('987654321098765', user.cns)
            self.assertEqual('CRM 123 / CE', user.crm)
            self.assertTrue(user.check_password('senha-legada-maior'))

    def test_profile_rejects_invalid_or_duplicate_identifiers(self):
        client = self.app.test_client()
        self._login(client)
        invalid = client.post('/perfil', data={
            'action': 'update_profile',
            'current_pin': 'senha-legada-maior',
            'full_name': 'Médico Antigo',
            'cns': 'A23456789012345',
            'crm': '',
        })
        self.assertEqual(200, invalid.status_code)

        duplicate = client.post('/perfil', data={
            'action': 'update_profile',
            'current_pin': 'senha-legada-maior',
            'full_name': 'Médico Antigo',
            'cns': '123456789012345',
            'crm': '',
        })
        self.assertEqual(200, duplicate.status_code)

    def test_new_pin_must_have_six_digits(self):
        client = self.app.test_client()
        self._login(client)
        rejected = client.post('/perfil', data={
            'action': 'change_pin',
            'current_pin': 'senha-legada-maior',
            'new_pin': '12345',
            'confirm_pin': '12345',
        })
        self.assertEqual(200, rejected.status_code)

        accepted = client.post('/perfil', data={
            'action': 'change_pin',
            'current_pin': 'senha-legada-maior',
            'new_pin': '001234',
            'confirm_pin': '001234',
        })
        self.assertEqual(302, accepted.status_code)
        with self.app.app_context():
            user = User.query.filter_by(username='medico').one()
            self.assertTrue(user.check_password('001234'))
            self.assertFalse(user.must_change_password)


if __name__ == '__main__':
    unittest.main()
