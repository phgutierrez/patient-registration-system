import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty, SpecialtySettings
from src.models.user import User


class AccessSettingsRouteTests(unittest.TestCase):
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
            db.session.add(SpecialtySettings(specialty_id=specialty.id))
            admin = User(username='admin', password='012345', full_name='Admin', role='admin', specialty_id=specialty.id)
            db.session.add(admin)
            db.session.commit()
            self.specialty_id = specialty.id
            self.admin_id = admin.id
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.admin_id)
            session['_fresh'] = True
            session['specialty_slug'] = 'ortopedia'

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def test_saves_local_then_network_without_erasing_inactive_source(self):
        local_file = Path(self.tempdir.name) / 'patients.accdb'
        local_file.touch()
        url = f'/configuracoes/especialidade/{self.specialty_id}/settings'
        response = self.client.post(url, data={
            'access_enabled': 'on',
            'access_source': 'local',
            'access_local_path': str(local_file),
        })
        self.assertEqual(302, response.status_code)
        with self.app.app_context():
            settings = SpecialtySettings.query.one()
            self.assertEqual('local', settings.access_source)
            self.assertEqual(str(local_file), settings.access_local_path)

        response = self.client.post(url, data={
            'access_enabled': 'on',
            'access_source': 'network',
            'access_host': 'server-cpam',
            'access_share_path': r'share\patients',
            'access_filename': 'patients.accdb',
        })
        self.assertEqual(302, response.status_code)
        with self.app.app_context():
            settings = SpecialtySettings.query.one()
            self.assertEqual('network', settings.access_source)
            self.assertEqual(str(local_file), settings.access_local_path)
            self.assertEqual('server-cpam', settings.access_host)

    def test_native_picker_is_localhost_only(self):
        selected = str(Path(self.tempdir.name) / 'patients.accdb')
        Path(selected).touch()
        endpoint = '/configuracoes/access/select-local-file'
        with patch('src.routes.specialty_settings.pick_local_access_database', return_value=selected):
            local = self.client.post(endpoint, json={}, environ_base={'REMOTE_ADDR': '127.0.0.1'})
            remote = self.client.post(endpoint, json={}, environ_base={'REMOTE_ADDR': '192.168.1.20'})
        self.assertEqual(200, local.status_code)
        self.assertTrue(local.get_json()['selected'])
        self.assertEqual(403, remote.status_code)

    def test_settings_page_renders_both_source_options(self):
        response = self.client.get('/configuracoes/')
        self.assertEqual(200, response.status_code)
        self.assertIn('Arquivo em rede'.encode('utf-8'), response.data)
        self.assertIn('Arquivo local'.encode('utf-8'), response.data)


if __name__ == '__main__':
    unittest.main()
