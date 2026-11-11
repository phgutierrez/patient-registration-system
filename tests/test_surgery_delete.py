import json
import tempfile
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path

from src.app import create_app
from src.extensions import db
from src.models.calendar_event_status import CalendarEventStatus
from src.models.patient import Patient
from src.models.specialty import Specialty
from src.models.surgery_request import SurgeryRequest
from src.models.sync import SyncOutbox
from src.models.user import User


def _config(root: Path, *, sync=False, csrf=False):
    database = root / 'instance' / 'delete.db'
    database.parent.mkdir(parents=True, exist_ok=True)
    values = {
        'TESTING': True,
        'SECRET_KEY': 'surgery-delete-test-secret-key',
        'BASE_DIR': root,
        'INSTANCE_PATH': database.parent,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': csrf,
        'RATELIMIT_ENABLED': False,
        'PROTECTED_PDF_DIR': root / 'pdfs',
        'ADMIN_BOOTSTRAP_USERNAME': '',
        'ADMIN_BOOTSTRAP_PASSWORD': '',
        'SECURITY_HEADERS_ENABLED': False,
        'DESKTOP_MODE': False,
        'SYNC_ENABLED': sync,
    }
    if sync:
        values.update({
            'SYNC_ROOT': str(root / 'shared'),
            'SYNC_START_WORKER': False,
            'SYNC_INTERVAL_SECONDS': 5,
        })
    return type('DeleteConfig', (), values)


class SurgeryDeleteTests(unittest.TestCase):
    sync = False
    csrf = False

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.app = create_app(_config(Path(self.tempdir.name), sync=self.sync, csrf=self.csrf))
        with self.app.app_context():
            db.create_all()
            specialty = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            other_specialty = Specialty(slug='outra', name='Outra', is_active=True)
            db.session.add_all([specialty, other_specialty])
            db.session.flush()
            self.users = {}
            for username, role, name, sp in (
                ('autor', 'user', 'Dr Autor', specialty),
                ('colega', 'user', 'Dr Colega', specialty),
                ('admin', 'admin', 'Administrador', specialty),
                ('externo', 'user', 'Dr Externo', other_specialty),
            ):
                user = User(username=username, password='012345', full_name=name,
                            role=role, specialty_id=sp.id)
                db.session.add(user)
                db.session.flush()
                self.users[username] = user.id
            patient = Patient(
                nome='Paciente Teste', prontuario='1234',
                data_nascimento=datetime(1980, 1, 2), sexo='M',
                nome_mae='Mãe Teste', cns='123456789012345',
                cidade='Fortaleza', contato='85999999999', estado='CE',
                diagnostico='Gonartrose', cid='M17', specialty_id=specialty.id,
            )
            db.session.add(patient)
            db.session.flush()
            self.patient_id = patient.id
            self.specialty_id = specialty.id
            self.mine = self._surgery(created_by=self.users['autor'], assistente='Outro')
            self.assisted = self._surgery(created_by=self.users['admin'], assistente='Dr Autor')
            self.foreign = self._surgery(created_by=self.users['colega'], assistente='Dr Colega')
            self.scheduled = self._surgery(created_by=self.users['autor'], assistente='', calendar_status='agendado')
            self.legacy = self._surgery(created_by=None, assistente='')
            db.session.commit()
            db.session.add(CalendarEventStatus(
                event_uid='evt-1', event_date=date.today(), status='PENDENTE',
                surgery_request_id=self.mine,
            ))
            db.session.commit()
        self.client = self.app.test_client()

    def _surgery(self, *, created_by, assistente, calendar_status=None, days=3):
        surgery = SurgeryRequest(
            patient_id=self.patient_id, specialty_id=self.specialty_id,
            peso=70, sinais_sintomas='Dor', condicoes_justificativa='Artrose',
            resultados_diagnosticos='RX', procedimento_solicitado='Artroplastia', codigo_procedimento='0408050063',
            tipo_cirurgia='Eletiva', data_cirurgia=date.today() + timedelta(days=days),
            hora_cirurgia=time(8, 0), assistente=assistente, duracao_prevista='2 horas',
            status='Pendente', calendar_status=calendar_status,
            created_by_user_id=created_by,
        )
        db.session.add(surgery)
        db.session.flush()
        return surgery.id

    def tearDown(self):
        if self.sync:
            from src.sync import sync_service
            sync_service.stop()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def login(self, username):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.users[username])
            session['_fresh'] = True
            session['specialty_slug'] = 'ortopedia'
            session['desktop_runtime_id'] = self.app.config['DESKTOP_RUNTIME_ID']

    def alive(self, surgery_id):
        with self.app.app_context():
            row = db.session.get(SurgeryRequest, surgery_id)
            return row is not None and not row.sync_deleted


class DeletePermissionTests(SurgeryDeleteTests):
    def test_author_deletes_own_request_and_unlinks_calendar_status(self):
        self.login('autor')
        response = self.client.post(f'/surgery/{self.mine}/delete')
        self.assertEqual(302, response.status_code)
        self.assertIn(f'/patients/patient/{self.patient_id}', response.headers['Location'])
        self.assertFalse(self.alive(self.mine))
        with self.app.app_context():
            status = CalendarEventStatus.query.filter_by(event_uid='evt-1').one()
            self.assertIsNone(status.surgery_request_id)

    def test_other_user_cannot_delete(self):
        self.login('colega')
        response = self.client.post(f'/surgery/{self.mine}/delete')
        self.assertEqual(302, response.status_code)
        self.assertTrue(self.alive(self.mine))

    def test_assistant_is_not_author_for_delete(self):
        self.login('autor')
        self.client.post(f'/surgery/{self.assisted}/delete')
        self.assertTrue(self.alive(self.assisted))

    def test_admin_deletes_any_request_including_legacy(self):
        self.login('admin')
        self.client.post(f'/surgery/{self.foreign}/delete')
        self.client.post(f'/surgery/{self.legacy}/delete')
        self.assertFalse(self.alive(self.foreign))
        self.assertFalse(self.alive(self.legacy))

    def test_legacy_without_author_only_admin(self):
        self.login('autor')
        self.client.post(f'/surgery/{self.legacy}/delete')
        self.assertTrue(self.alive(self.legacy))

    def test_other_specialty_is_forbidden(self):
        self.login('externo')
        response = self.client.post(f'/surgery/{self.mine}/delete')
        self.assertEqual(403, response.status_code)
        self.assertTrue(self.alive(self.mine))

    def test_get_is_not_allowed(self):
        self.login('autor')
        self.assertEqual(405, self.client.get(f'/surgery/{self.mine}/delete').status_code)

    def test_scheduled_request_warns_about_google_calendar(self):
        self.login('autor')
        response = self.client.post(f'/surgery/{self.scheduled}/delete', follow_redirects=True)
        self.assertFalse(self.alive(self.scheduled))
        self.assertIn('Google Agenda'.encode('utf-8'), response.data)

    def test_safe_next_redirect_only(self):
        self.login('admin')
        response = self.client.post(f'/surgery/{self.foreign}/delete', data={'next': '//evil.example'})
        self.assertNotIn('evil.example', response.headers['Location'])
        response = self.client.post(f'/surgery/{self.legacy}/delete', data={'next': '/pendencias?escopo=todas'})
        self.assertTrue(response.headers['Location'].endswith('/pendencias?escopo=todas'))

    def test_button_only_rendered_for_allowed_users(self):
        self.login('autor')
        page = self.client.get(f'/patients/patient/{self.patient_id}').get_data(as_text=True)
        self.assertIn(f'data-delete-surgery="{self.mine}"', page)
        self.assertNotIn(f'data-delete-surgery="{self.foreign}"', page)
        self.assertNotIn(f'data-delete-surgery="{self.legacy}"', page)
        self.assertIn('confirm-delete.js', page)
        confirmation = self.client.get(f'/surgery/{self.scheduled}/confirmation').get_data(as_text=True)
        self.assertIn('data-scheduled="1"', confirmation)


class DashboardAndPendingTests(SurgeryDeleteTests):
    def test_dashboard_counts_mine_as_author_or_assistant(self):
        self.login('autor')
        page = self.client.get('/index').get_data(as_text=True)
        # mine + assisted + scheduled = 3 (foreign e legacy são de outros)
        self.assertIn('<strong>3</strong><small>Minhas solicitações pendentes · 5 na especialidade', page)
        self.assertIn('href="/pendencias"', page)

    def test_deleted_request_disappears_from_dashboard(self):
        self.login('autor')
        self.client.post(f'/surgery/{self.mine}/delete')
        page = self.client.get('/index').get_data(as_text=True)
        self.assertIn('<strong>2</strong><small>Minhas solicitações pendentes · 4 na especialidade', page)

    def test_pending_page_scopes(self):
        self.login('autor')
        mine = self.client.get('/pendencias').get_data(as_text=True)
        self.assertIn('Solicitações pendentes', mine)
        self.assertIn(f'/surgery/{self.assisted}/confirmation', mine)
        self.assertNotIn(f'/surgery/{self.foreign}/confirmation', mine)
        everything = self.client.get('/pendencias?escopo=todas').get_data(as_text=True)
        self.assertIn(f'/surgery/{self.foreign}/confirmation', everything)
        self.assertIn(f'/surgery/{self.legacy}/confirmation', everything)

    def test_pending_page_respects_specialty(self):
        self.login('externo')
        with self.client.session_transaction() as session:
            session['specialty_slug'] = 'outra'
        page = self.client.get('/pendencias?escopo=todas').get_data(as_text=True)
        self.assertNotIn(f'/surgery/{self.mine}/confirmation', page)


class DeleteWithCsrfTests(SurgeryDeleteTests):
    csrf = True

    def test_missing_csrf_token_is_rejected(self):
        self.login('autor')
        response = self.client.post(f'/surgery/{self.mine}/delete')
        self.assertEqual(400, response.status_code)
        self.assertTrue(self.alive(self.mine))


class DeleteWithSyncTests(SurgeryDeleteTests):
    sync = True

    def test_delete_becomes_tombstone_with_outbox_event(self):
        # Sem pareamento, as rotas redirecionam para a configuração do sync;
        # por isso a view é chamada diretamente, com o usuário autenticado.
        from flask_login import login_user
        from src.routes.surgery import delete_surgery_request
        with self.app.app_context():
            sync_uuid = db.session.get(SurgeryRequest, self.mine).sync_uuid
        with self.app.test_request_context(f'/surgery/{self.mine}/delete', method='POST'):
            login_user(db.session.get(User, self.users['autor']))
            response = delete_surgery_request(self.mine)
            self.assertEqual(302, response.status_code)
        with self.app.app_context():
            archived = SurgeryRequest.query.filter_by(sync_uuid=sync_uuid).one()
            self.assertTrue(archived.sync_deleted)
            events = [json.loads(row.payload_json) for row in SyncOutbox.query.all()]
            self.assertTrue(any(
                event.get('changes', {}).get('_deleted') for event in events
            ))
            status = CalendarEventStatus.query.filter_by(event_uid='evt-1').one()
            self.assertIsNone(status.surgery_request_id)


if __name__ == '__main__':
    unittest.main()
