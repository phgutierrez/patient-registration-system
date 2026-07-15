import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty, SpecialtyProcedure, SpecialtySettings
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
            session['desktop_runtime_id'] = self.app.config['DESKTOP_RUNTIME_ID']

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

    def test_new_procedure_is_appended_and_client_order_is_ignored(self):
        with self.app.app_context():
            db.session.add_all([
                SpecialtyProcedure(specialty_id=self.specialty_id, descricao='Primeiro', sort_order=2),
                SpecialtyProcedure(specialty_id=self.specialty_id, descricao='Segundo', sort_order=8),
            ])
            db.session.commit()

        response = self.client.post(
            f'/configuracoes/especialidade/{self.specialty_id}/procedimentos/add',
            data={'descricao': 'Novo no final', 'codigo_sus': '123', 'sort_order': '-100'},
        )
        self.assertEqual(302, response.status_code)
        with self.app.app_context():
            created = SpecialtyProcedure.query.filter_by(descricao='Novo no final').one()
            self.assertEqual(9, created.sort_order)

    def test_edit_does_not_accept_manual_order(self):
        with self.app.app_context():
            proc = SpecialtyProcedure(
                specialty_id=self.specialty_id, descricao='Original', sort_order=7,
            )
            db.session.add(proc)
            db.session.commit()
            proc_id = proc.id

        response = self.client.post(
            f'/configuracoes/procedimentos/{proc_id}/edit',
            data={'descricao': 'Atualizado', 'codigo_sus': '', 'sort_order': '0'},
        )
        self.assertEqual(302, response.status_code)
        with self.app.app_context():
            updated = db.session.get(SpecialtyProcedure, proc_id)
            self.assertEqual('Atualizado', updated.descricao)
            self.assertEqual(7, updated.sort_order)

    def test_procedure_list_uses_order_then_id_without_order_controls(self):
        with self.app.app_context():
            db.session.add_all([
                SpecialtyProcedure(specialty_id=self.specialty_id, descricao='Empate A', sort_order=4),
                SpecialtyProcedure(specialty_id=self.specialty_id, descricao='Empate B', sort_order=4),
            ])
            db.session.commit()
            specialty = db.session.get(Specialty, self.specialty_id)
            descriptions = [procedure.descricao for procedure in specialty.procedures]
            self.assertEqual(['Empate A', 'Empate B'], descriptions)

        response = self.client.get('/configuracoes/')
        self.assertEqual(200, response.status_code)
        self.assertNotIn(b'name="sort_order"', response.data)
        self.assertLess(response.data.index(b'Empate A'), response.data.index(b'Empate B'))

    def test_concurrent_procedures_receive_consecutive_final_positions(self):
        with self.app.app_context():
            db.session.add(SpecialtyProcedure(
                specialty_id=self.specialty_id, descricao='Existente', sort_order=10,
            ))
            db.session.commit()

        def add_one(index):
            client = self.app.test_client()
            with client.session_transaction() as session:
                session['_user_id'] = str(self.admin_id)
                session['_fresh'] = True
                session['specialty_slug'] = 'ortopedia'
                session['desktop_runtime_id'] = self.app.config['DESKTOP_RUNTIME_ID']
            return client.post(
                f'/configuracoes/especialidade/{self.specialty_id}/procedimentos/add',
                data={'descricao': f'Concorrente {index}', 'sort_order': '-1'},
            ).status_code

        with ThreadPoolExecutor(max_workers=4) as executor:
            statuses = list(executor.map(add_one, range(4)))
        self.assertEqual([302, 302, 302, 302], statuses)

        with self.app.app_context():
            created = (
                SpecialtyProcedure.query
                .filter(SpecialtyProcedure.descricao.like('Concorrente %'))
                .order_by(SpecialtyProcedure.sort_order, SpecialtyProcedure.id)
                .all()
            )
            self.assertEqual([11, 12, 13, 14], [item.sort_order for item in created])


if __name__ == '__main__':
    unittest.main()
