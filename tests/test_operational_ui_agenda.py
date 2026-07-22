import tempfile
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytz

from src.app import create_app
from src.extensions import db
from src.models.calendar_event_status import CalendarEventStatus
from src.models.patient import Patient
from src.models.specialty import Specialty, SpecialtyProcedure, SpecialtySettings
from src.models.surgery_request import SurgeryRequest
from src.models.user import User
from src.services.calendar_cache_service import (
    CalendarCacheService, CalendarData,
)
from src.services.calendar_service import CalendarService


class OperationalUiAgendaTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        database = Path(self.tempdir.name) / 'ui.db'

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
            GOOGLE_CALENDAR_TZ = 'America/Fortaleza'
            CALENDAR_CACHE_TTL_SECONDS = 300

        self.app = create_app(TestConfig)
        with self.app.app_context():
            db.create_all()
            specialty = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            db.session.add(specialty)
            db.session.flush()
            db.session.add(SpecialtySettings(
                specialty_id=specialty.id,
                agenda_url='https://calendar.invalid/public.ics',
            ))
            db.session.add(SpecialtyProcedure(
                specialty_id=specialty.id,
                descricao='Artroplastia de joelho',
                codigo_sus='0408050063',
                sort_order=1,
            ))
            user = User(
                username='admin', password='012345', full_name='Administrador',
                role='admin', specialty_id=specialty.id,
            )
            patient = Patient(
                nome='Paciente Teste', prontuario='1234',
                data_nascimento=datetime(1980, 1, 2), sexo='M',
                nome_mae='Mãe Teste', cns='123456789012345',
                cidade='Fortaleza', contato='85999999999',
                diagnostico='Gonartrose', cid='M17',
                specialty_id=specialty.id,
            )
            db.session.add_all([user, patient])
            db.session.flush()
            first = self._new_surgery(patient.id, specialty.id, 'Pendente', 'agendado', 2)
            second = self._new_surgery(patient.id, specialty.id, 'Realizada', None, 5)
            db.session.add_all([first, second])
            db.session.commit()
            self.user_id = user.id
            self.patient_id = patient.id
            self.specialty_id = specialty.id
            self.surgery_id = first.id

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.user_id)
            session['_fresh'] = True
            session['specialty_slug'] = 'ortopedia'
            session['desktop_runtime_id'] = self.app.config['DESKTOP_RUNTIME_ID']

    @staticmethod
    def _new_surgery(patient_id, specialty_id, status, calendar_status, days):
        return SurgeryRequest(
            patient_id=patient_id, specialty_id=specialty_id,
            peso=70, sinais_sintomas='Dor', condicoes_justificativa='Artrose',
            resultados_diagnosticos='Radiografia', procedimento_solicitado='Artroplastia de joelho',
            codigo_procedimento='0408050063', tipo_cirurgia='Eletiva',
            data_cirurgia=date.today() + timedelta(days=days),
            hora_cirurgia=time(8, 0), assistente='Administrador',
            duracao_prevista='2 horas', status=status,
            calendar_status=calendar_status,
        )

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def _event(self, *, uid='event-1', description=None):
        timezone = pytz.timezone('America/Fortaleza')
        start = timezone.localize(datetime.combine(
            date.today() + timedelta(days=2), time(8, 0)
        ))
        return {
            'uid': uid,
            'title': 'Artroplastia de joelho',
            'start': start,
            'end': start + timedelta(hours=2),
            'all_day': False,
            'location': 'Centro cirúrgico',
            'description': description or f'Prontuário: 1234\n[SOLICITACAO:{self.surgery_id}]',
        }

    def _fake_cache(self, events):
        service = Mock()
        service.calendar_service = CalendarService(
            'specialty-test',
            ics_url='https://calendar.invalid/public.ics',
        )
        service.get_calendar_data.return_value = CalendarData(
            events,
            service.calendar_service.group_events_by_day(events),
            datetime.utcnow(),
            'ok',
            None,
        )
        return service

    def test_dashboard_uses_local_data_and_renders_operational_summary(self):
        with patch('requests.get') as external:
            response = self.client.get('/index')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Vis\xc3\xa3o geral do consult\xc3\xb3rio', response.data)
        self.assertIn(b'Pr\xc3\xb3ximos procedimentos', response.data)
        self.assertIn(b'Paciente Teste', response.data)
        external.assert_not_called()

    def test_patient_list_and_request_use_new_compact_assets(self):
        response = self.client.get('/patients/patients?q=1234')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'app-page-header page-heading', response.data)
        self.assertIn(b'patient-actions', response.data)
        self.assertIn(b'Solicitar', response.data)
        response = self.client.get(f'/patient/{self.patient_id}/surgery/request')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'surgery-request.css', response.data)
        self.assertIn(b'app-page-header request-heading', response.data)
        self.assertIn(b'Localizar procedimento', response.data)
        self.assertNotIn(b'prompt(', response.data)

    def test_shared_shell_uses_modern_headers_and_single_sidebar_controller(self):
        response = self.client.get('/index')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'css/app-shell.css', response.data)
        self.assertIn(b'js/app-shell.js', response.data)
        self.assertNotIn(b'css/styles.css', response.data)
        self.assertIn(b'app-page-header page-heading', response.data)
        self.assertIn(b'id="appSidebar"', response.data)
        self.assertIn(b'aria-current="page"', response.data)
        self.assertNotIn(b'<style>', response.data)

        source = (Path(__file__).resolve().parents[1] / 'src' / 'static' / 'js' / 'app-shell.js').read_text(encoding='utf-8')
        legacy_css = (Path(__file__).resolve().parents[1] / 'src' / 'static' / 'css' / 'styles.css').read_text(encoding='utf-8')
        self.assertEqual(1, source.count("menuToggle?.addEventListener('click'"))
        self.assertIn("storedState === null ? true", source)
        self.assertIn("event.key === 'Escape'", source)
        self.assertNotIn('header {', legacy_css)
        self.assertNotIn('form {', legacy_css)

    def test_new_patient_uses_compact_assets_and_preserves_access_lookup(self):
        response = self.client.get('/patients/patient/new')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'css/pages/patient-new.css', response.data)
        self.assertIn(b'js/pages/patient-new.js', response.data)
        self.assertIn(b'id="formErrorSummary"', response.data)
        self.assertIn(b'id="btnBuscaAccess"', response.data)
        self.assertIn(b'/patients/api/search-patient-accdb', response.data)
        self.assertIn(b'name="nome_mae"', response.data)
        self.assertNotIn(b'[Init]', response.data)
        self.assertNotIn(b'<style>', response.data)

    def test_specialty_selection_uses_system_logo_instead_of_bone_icon(self):
        anonymous = self.app.test_client()
        response = anonymous.get('/')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'specialty-card-logo', response.data)
        self.assertIn(b'logo%20ortoped.png', response.data)
        self.assertNotIn(b'fa-bone', response.data)

    def test_agenda_renders_cached_event_and_remembers_view(self):
        event = self._event()
        fake = self._fake_cache([event])
        with patch(
            'src.services.calendar_cache_service.get_calendar_cache_service',
            return_value=fake,
        ):
            response = self.client.get('/agenda?view=week')
            second = self.client.get('/agenda')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'Artroplastia de joelho', response.data)
        self.assertIn(b'eventStatusForm', response.data)
        self.assertIn(b'app-page-header agenda-heading', response.data)
        self.assertIn(b'data-view="week"', second.data)

    def test_status_is_optional_for_suspension_and_syncs_linked_request(self):
        event = self._event()
        fake = self._fake_cache([event])
        with patch(
            'src.services.calendar_cache_service.get_calendar_cache_service',
            return_value=fake,
        ):
            response = self.client.post('/agenda/events/status', json={
                'event_uid': event['uid'],
                'event_date': (date.today() + timedelta(days=2)).isoformat(),
                'status': 'SUSPENSA',
                'reason': '',
            })
            self.assertEqual(200, response.status_code, response.get_data(as_text=True))
            self.assertTrue(response.get_json()['request_sync']['matched'])
            reset = self.client.post('/agenda/events/status', json={
                'event_uid': event['uid'],
                'event_date': (date.today() + timedelta(days=2)).isoformat(),
                'status': 'PENDENTE',
            })
            self.assertEqual(200, reset.status_code)

        with self.app.app_context():
            surgery = db.session.get(SurgeryRequest, self.surgery_id)
            saved = CalendarEventStatus.query.filter_by(event_uid=event['uid']).one()
            self.assertEqual('Pendente', surgery.status)
            self.assertEqual('PENDENTE', saved.status)
            self.assertEqual(self.surgery_id, saved.surgery_request_id)

    def test_unmatched_event_updates_only_agenda(self):
        event = self._event(uid='external-event', description='Evento externo sem referência')
        fake = self._fake_cache([event])
        with patch(
            'src.services.calendar_cache_service.get_calendar_cache_service',
            return_value=fake,
        ):
            response = self.client.post('/agenda/events/status', json={
                'event_uid': event['uid'],
                'event_date': (date.today() + timedelta(days=2)).isoformat(),
                'status': 'REALIZADA',
            })
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.get_json()['request_sync']['matched'])

    def test_warm_calendar_cache_does_not_fetch_twice(self):
        class Response:
            status_code = 200
            text = (
                'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\n'
                'UID:cache-event\r\nDTSTART:20300101T120000Z\r\n'
                'DTEND:20300101T130000Z\r\nSUMMARY:Teste\r\n'
                'END:VEVENT\r\nEND:VCALENDAR\r\n'
            )
            headers = {'ETag': 'test-etag'}
            def raise_for_status(self):
                return None

        with self.app.app_context(), patch(
            'src.services.calendar_cache_service.requests.get',
            return_value=Response(),
        ) as fetch:
            service = CalendarCacheService(
                'specialty-cache',
                'https://calendar.invalid/cache.ics',
            )
            first = service.get_calendar_data()
            second = service.get_calendar_data()
            self.assertEqual(1, len(first.events))
            self.assertEqual(first.events, second.events)
            self.assertEqual(1, fetch.call_count)

    def test_expired_cache_is_returned_before_background_refresh(self):
        with self.app.app_context():
            service = CalendarCacheService(
                'specialty-stale',
                'https://calendar.invalid/stale.ics',
            )
            service._memory_cache = CalendarData(
                [], {}, datetime.utcnow() - timedelta(minutes=10), 'ok', None
            )
            with patch.object(service, '_start_background_refresh') as start:
                result = service.get_calendar_data()
            self.assertEqual('stale', result.source_status)
            start.assert_called_once()


if __name__ == '__main__':
    unittest.main()
