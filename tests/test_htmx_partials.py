"""Respostas parciais HTMX e fallback tradicional (lista de pacientes e agenda)."""
import re
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import requests

from src.app import create_app
from src.extensions import db
from src.models.patient import Patient
from src.models.specialty import Specialty, SpecialtySettings
from src.models.user import User
from src.services.calendar_cache_service import CalendarCacheService
from tests import test_operational_ui_agenda as _base

HX = {'HX-Request': 'true'}
CACHE_TARGET = 'src.services.calendar_cache_service.get_calendar_cache_service'


class _AppFixture(unittest.TestCase):
    """Reaproveita o app/semente de OperationalUiAgendaTests sem herdar seus testes."""

    setUp = _base.OperationalUiAgendaTests.setUp
    tearDown = _base.OperationalUiAgendaTests.tearDown
    _new_surgery = staticmethod(_base.OperationalUiAgendaTests._new_surgery)
    _event = _base.OperationalUiAgendaTests._event
    _fake_cache = _base.OperationalUiAgendaTests._fake_cache

    def _add_patients(self, *items, specialty_id=None):
        with self.app.app_context():
            for nome, prontuario in items:
                db.session.add(Patient(
                    nome=nome, prontuario=prontuario,
                    data_nascimento=datetime(1990, 5, 6), sexo='F',
                    nome_mae='Mãe', cns='', cidade='João Pessoa', contato='',
                    diagnostico='', cid='',
                    specialty_id=specialty_id or self.specialty_id,
                ))
            db.session.commit()

    def _login(self, client, user_id):
        with client.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['_fresh'] = True
            session['specialty_slug'] = 'ortopedia'
            session['desktop_runtime_id'] = self.app.config['DESKTOP_RUNTIME_ID']


class PatientListPartialTests(_AppFixture):
    def test_full_page_fallback_has_shell_form_and_results(self):
        response = self.client.get('/patients/patients')
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertIn('<html', html)
        self.assertIn('id="appSidebar"', html)
        self.assertIn('id="patient-results"', html)
        # Formulário tradicional (GET) continua presente para uso sem JS.
        self.assertIn('method="get" action="/patients/patients"', html)
        self.assertIn('hx-get="/patients/patients"', html)
        self.assertIn('Paciente Teste', html)
        self.assertIn('HX-Request', response.headers.get('Vary', ''))

    def test_htmx_request_returns_only_results_fragment(self):
        response = self.client.get('/patients/patients?q=Paciente', headers=HX)
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertNotIn('<html', html)
        self.assertNotIn('appSidebar', html)
        self.assertIn('Paciente Teste', html)
        self.assertIn('id="patientResultCount"', html)
        self.assertIn('hx-swap-oob="true"', html)
        self.assertIn('HX-Request', response.headers.get('Vary', ''))
        # Exclusão segue protegida por formulário POST com token CSRF.
        self.assertRegex(html, r'<form id="delete-form-\d+" action="/patients/patient/\d+/delete" method="post"')
        self.assertIn('name="csrf_token"', html)

    def test_history_restore_receives_full_page(self):
        response = self.client.get(
            '/patients/patients',
            headers={**HX, 'HX-History-Restore-Request': 'true'},
        )
        self.assertIn('<html', response.get_data(as_text=True))

    def test_exact_prontuario_has_priority_over_partial_matches(self):
        self._add_patients(('Outro Paciente', '91234'), ('Mais Um', '12345'))
        html = self.client.get('/patients/patients?q=1234', headers=HX).get_data(as_text=True)
        self.assertIn('Paciente Teste', html)
        self.assertNotIn('Outro Paciente', html)
        self.assertNotIn('Mais Um', html)
        self.assertIn('1 paciente<', html)

        partial = self.client.get('/patients/patients?q=Paciente', headers=HX).get_data(as_text=True)
        self.assertIn('Outro Paciente', partial)

    def test_server_side_pagination_with_htmx_links(self):
        self._add_patients(*[(f'Paciente Lote {index:02d}', f'50{index:02d}') for index in range(25)])
        first = self.client.get('/patients/patients', headers=HX).get_data(as_text=True)
        self.assertIn('Página 1 de 2', first)
        self.assertIn('26 pacientes', first)
        # Nunca envia todos os pacientes ao navegador: 20 por página.
        self.assertEqual(20, len(re.findall(r'class="patient-mobile-row"', first)))
        self.assertIn('hx-get="/patients/patients?page=2"', first)

        second = self.client.get('/patients/patients?page=2', headers=HX).get_data(as_text=True)
        self.assertIn('Página 2 de 2', second)
        self.assertEqual(6, len(re.findall(r'class="patient-mobile-row"', second)))
        self.assertIn('aria-current="page">2<', second)

    def test_empty_state(self):
        html = self.client.get('/patients/patients?q=inexistente', headers=HX).get_data(as_text=True)
        self.assertIn('Nenhum paciente encontrado', html)
        self.assertIn('0 pacientes', html)

    def test_specialty_scope_is_preserved_for_non_admin(self):
        with self.app.app_context():
            other = Specialty(slug='pediatria', name='Pediatria', is_active=True)
            db.session.add(other)
            db.session.flush()
            other_id = other.id
            user = User(
                username='medico', password='012345', full_name='Médico',
                role='solicitante', specialty_id=self.specialty_id,
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        self._add_patients(('Paciente de Outra Especialidade', '7777'), specialty_id=other_id)
        client = self.app.test_client()
        self._login(client, user_id)
        html = client.get('/patients/patients', headers=HX).get_data(as_text=True)
        self.assertIn('Paciente Teste', html)
        self.assertNotIn('Outra Especialidade', html)

    def test_anonymous_and_logged_out_users_are_redirected(self):
        anonymous = self.app.test_client()
        response = anonymous.get('/patients/patients', headers=HX)
        self.assertEqual(302, response.status_code)

        self.client.get('/logout')
        after_logout = self.client.get('/patients/patients', headers=HX)
        self.assertEqual(302, after_logout.status_code)


class AgendaPartialTests(_AppFixture):
    def _get(self, url, fake, headers=None):
        with patch(CACHE_TARGET, return_value=fake):
            return self.client.get(url, headers=headers or {})

    def test_htmx_returns_agenda_app_fragment_without_modal(self):
        response = self._get('/agenda?view=week', self._fake_cache([self._event()]), HX)
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertNotIn('<html', html)
        self.assertIn('<div id="agendaApp"', html)
        self.assertIn('hx-target="this" hx-swap="outerHTML"', html)
        self.assertIn('Artroplastia de joelho', html)
        # O modal Bootstrap fica fora da região trocada.
        self.assertNotIn('id="eventModal"', html)
        self.assertIn('HX-Request', response.headers.get('Vary', ''))

    def test_full_page_fallback_keeps_modal_and_links(self):
        response = self._get('/agenda?view=week', self._fake_cache([self._event()]))
        html = response.get_data(as_text=True)
        self.assertIn('<html', html)
        self.assertIn('id="eventModal"', html)
        self.assertIn('bootstrap.bundle.min.js', html)
        self.assertIn('id="agendaPeriodNext" href="/agenda?', html)

    def test_period_navigation_is_computed_on_server(self):
        today = date.today()
        html = self._get('/agenda?view=week', self._fake_cache([]), HX).get_data(as_text=True)
        previous = (today - timedelta(days=7)).isoformat()
        following = (today + timedelta(days=7)).isoformat()
        self.assertIn(f'start={previous}', html)
        self.assertIn(f'end={(today - timedelta(days=1)).isoformat()}', html)
        self.assertIn(f'start={following}', html)

        month = self._get(
            '/agenda?view=month&month=2026-01&status=realizada&q=joelho',
            self._fake_cache([]), HX,
        ).get_data(as_text=True)
        self.assertIn('month=2025-12', month)
        self.assertIn('month=2026-02', month)
        self.assertIn(f'month={today:%Y-%m}', month)
        # Filtros ativos são preservados nos links de navegação.
        self.assertRegex(month, r'href="/agenda\?[^"]*status=realizada')
        self.assertRegex(month, r'href="/agenda\?[^"]*q=joelho')

    def test_stale_cache_shows_refresh_notice(self):
        fake = self._fake_cache([self._event()])
        fake.get_calendar_data.return_value = fake.get_calendar_data.return_value._replace(
            source_status='stale'
        )
        html = self._get('/agenda', fake, HX).get_data(as_text=True)
        self.assertIn('Atualizando agenda.', html)
        self.assertIn('Artroplastia de joelho', html)

    def test_network_failure_without_cache_shows_error(self):
        with self.app.app_context():
            service = CalendarCacheService('specialty-offline', 'https://calendar.invalid/offline.ics')
        with patch(
            'src.services.calendar_cache_service.requests.get',
            side_effect=requests.ConnectionError('sem rede'),
        ):
            for headers in (HX, {}):
                with self.subTest(htmx=bool(headers)):
                    response = self._get('/agenda', service, headers)
                    self.assertEqual(200, response.status_code)
                    self.assertIn('Agenda indisponível.', response.get_data(as_text=True))

    def test_not_configured_agenda_keeps_400_for_page_and_partial(self):
        with self.app.app_context():
            SpecialtySettings.query.update({'agenda_url': None})
            db.session.commit()
        for headers in (HX, {}):
            with self.subTest(htmx=bool(headers)):
                response = self.client.get('/agenda', headers=headers)
                self.assertEqual(400, response.status_code)
                self.assertIn('Agenda não configurada', response.get_data(as_text=True))

    def test_refresh_requires_admin(self):
        with self.app.app_context():
            user = User(
                username='medico2', password='012345', full_name='Médico',
                role='solicitante', specialty_id=self.specialty_id,
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        client = self.app.test_client()
        self._login(client, user_id)
        with patch(CACHE_TARGET, return_value=self._fake_cache([])):
            response = client.post('/agenda/cache/refresh', headers=HX)
        self.assertEqual(403, response.status_code)


class HtmxCsrfTests(_AppFixture):
    def setUp(self):
        super().setUp()
        self.app.config['WTF_CSRF_ENABLED'] = True

    def _token(self):
        html = self.client.get('/patients/patients').get_data(as_text=True)
        return re.search(r'<meta name="csrf-token" content="([^"]+)"', html).group(1)

    def test_htmx_post_without_token_is_rejected(self):
        with patch(CACHE_TARGET, return_value=self._fake_cache([])):
            response = self.client.post('/agenda/cache/refresh', headers=HX)
        self.assertEqual(400, response.status_code)

    def test_htmx_post_with_header_token_is_accepted(self):
        token = self._token()
        with patch(CACHE_TARGET, return_value=self._fake_cache([])):
            response = self.client.post(
                '/agenda/cache/refresh', headers={**HX, 'X-CSRFToken': token}
            )
        self.assertEqual(200, response.status_code, response.get_data(as_text=True))

    def test_patient_delete_still_requires_token(self):
        rejected = self.client.post(f'/patients/patient/{self.patient_id}/delete')
        self.assertEqual(400, rejected.status_code)
        with self.app.app_context():
            self.assertIsNotNone(db.session.get(Patient, self.patient_id))

        html = self.client.get('/patients/patients', headers=HX).get_data(as_text=True)
        form_token = re.search(
            rf'id="delete-form-{self.patient_id}"[^>]*>.*?name="csrf_token" value="([^"]+)"',
            html,
        ).group(1)
        accepted = self.client.post(
            f'/patients/patient/{self.patient_id}/delete', data={'csrf_token': form_token}
        )
        self.assertEqual(302, accepted.status_code)


if __name__ == '__main__':
    unittest.main()
