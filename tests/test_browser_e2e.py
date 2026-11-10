"""Teste de ponta a ponta no navegador (Chromium headless via Playwright).

Opcional: é ignorado quando o Playwright/Chromium não está instalado.
    pip install -r requirements-e2e.txt
    python -m playwright install chromium

Roda com CSRF ativo e CSP aplicada; qualquer erro de JavaScript, violação de
CSP ou requisição para fora do servidor local faz o teste falhar.
"""
import socket
import tempfile
import threading
import unittest
from datetime import date, datetime, time, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:  # pragma: no cover - dependência opcional
    expect = sync_playwright = None

import pytz
from werkzeug.serving import make_server

from src.app import create_app
from src.extensions import db
from src.models.patient import Patient
from src.models.specialty import Specialty, SpecialtySettings
from src.models.surgery_request import SurgeryRequest
from src.models.user import User
from src.services.calendar_cache_service import CalendarData
from src.services.calendar_service import CalendarService


def _browser_available():
    if sync_playwright is None:
        return False
    try:
        with sync_playwright() as playwright:
            playwright.chromium.launch().close()
        return True
    except Exception:
        return False


BROWSER_AVAILABLE = _browser_available()


def _free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


@unittest.skipUnless(BROWSER_AVAILABLE, 'Playwright/Chromium não instalados (requirements-e2e.txt).')
class BrowserEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        folder = Path(cls.tempdir.name)

        class Config:
            SECRET_KEY = 'browser-e2e-secret-key-that-is-long-enough'
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{folder}/e2e.db'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = True
            RATELIMIT_ENABLED = False
            PROTECTED_PDF_DIR = folder / 'pdfs'
            ADMIN_BOOTSTRAP_USERNAME = ''
            ADMIN_BOOTSTRAP_PASSWORD = ''
            SECURITY_HEADERS_ENABLED = True
            SECURITY_CSP_ENFORCE = True
            DESKTOP_MODE = False
            SYNC_ENABLED = False
            GOOGLE_CALENDAR_TZ = 'America/Fortaleza'

        from src.config import Config as BaseConfig
        Config.SECURITY_CSP_REPORT_ONLY_POLICY = BaseConfig.SECURITY_CSP_REPORT_ONLY_POLICY
        cls.app = create_app(Config)
        with cls.app.app_context():
            db.create_all()
            specialty = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            db.session.add(specialty)
            db.session.flush()
            db.session.add(SpecialtySettings(
                specialty_id=specialty.id, agenda_url='https://calendar.invalid/e2e.ics'
            ))
            user = User(username='admin', password='012345', full_name='Admin',
                        role='admin', specialty_id=specialty.id)
            db.session.add(user)
            for index in range(27):
                db.session.add(Patient(
                    nome=f'Paciente {index:02d}', prontuario=f'{1000 + index}',
                    data_nascimento=datetime(2015, 1, 1), sexo='M', nome_mae='Mãe',
                    cns='', cidade='Cidade', contato='', diagnostico='', cid='',
                    specialty_id=specialty.id,
                ))
            db.session.commit()
            user_id = user.id
            patient = Patient.query.filter_by(prontuario='1026').one()
            surgery = SurgeryRequest(
                patient_id=patient.id, specialty_id=specialty.id, peso=30,
                sinais_sintomas='Dor', condicoes_justificativa='Indicação',
                resultados_diagnosticos='RX', procedimento_solicitado='Osteotomia',
                codigo_procedimento='0408040158', tipo_cirurgia='Eletiva',
                data_cirurgia=date.today() + timedelta(days=5), hora_cirurgia=time(8, 0),
                internar_antes=True, assistente='Admin', duracao_prevista='2 horas',
                reserva_sangue=True, quantidade_sangue='1 CH', reserva_uti=True,
                status='Pendente', created_by_user_id=user.id,
            )
            db.session.add(surgery)
            db.session.flush()
            from src.pdf.snapshots import create_request_snapshots
            create_request_snapshots(patient, surgery, user)
            db.session.commit()
            cls.patient_id, cls.surgery_id = patient.id, surgery.id

        timezone = pytz.timezone('America/Fortaleza')

        def event(uid, days, title):
            start = timezone.localize(datetime.combine(date.today() + timedelta(days=days), time(8)))
            return {'uid': uid, 'title': title, 'start': start, 'end': start + timedelta(hours=2),
                    'all_day': False, 'location': 'CC', 'description': 'Descrição'}

        events = [event('e1', 1, 'Cirurgia Semana Atual'), event('e2', 9, 'Cirurgia Semana Seguinte')]
        fake = Mock()
        fake.calendar_service = CalendarService('e2e', ics_url='https://calendar.invalid/e2e.ics')
        fake.get_calendar_data.side_effect = lambda force_refresh=False: CalendarData(
            events, fake.calendar_service.group_events_by_day(events), datetime.utcnow(), 'ok', None)
        cls.patcher = patch(
            'src.services.calendar_cache_service.get_calendar_cache_service', return_value=fake
        )
        cls.patcher.start()

        port = _free_port()
        cls.base = f'http://127.0.0.1:{port}'
        cls.server = make_server('127.0.0.1', port, cls.app, threaded=True)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.cookie = cls.app.session_interface.get_signing_serializer(cls.app).dumps({
            '_user_id': str(user_id), '_fresh': True, 'specialty_slug': 'ortopedia',
            'desktop_runtime_id': cls.app.config['DESKTOP_RUNTIME_ID'],
        })
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.patcher.stop()
        cls.tempdir.cleanup()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1366, 'height': 900})
        self.context.add_cookies([{'name': 'session', 'value': self.cookie, 'url': self.base}])
        self.page = self.context.new_page()
        self.problems, self.external, self.documents = [], [], []
        self.page.on('console', lambda message: self.problems.append(message.text)
                     if message.type == 'error' else None)
        self.page.on('pageerror', lambda error: self.problems.append(str(error)))
        self.page.on('request', self._track_request)

    def _track_request(self, request):
        if not request.url.startswith(self.base) and not request.url.startswith('data:'):
            self.external.append(request.url)
        if request.resource_type == 'document':
            self.documents.append(request.url)

    def tearDown(self):
        self.context.close()
        self.assertEqual([], self.problems, 'Erros de JavaScript/CSP no console')
        self.assertEqual([], self.external, 'Requisições externas (CDN?)')

    def _mark_page(self):
        self.page.evaluate('window.__semRecarregar = true')
        self.documents.clear()

    def _assert_no_reload(self):
        self.assertTrue(self.page.evaluate('window.__semRecarregar === true'))
        self.assertEqual([], self.documents)

    def test_patient_search_pagination_and_delete(self):
        page = self.page
        page.goto(f'{self.base}/patients/patients')
        self.assertGreater(page.locator('svg.icon use').count(), 5)
        self._mark_page()
        with page.expect_response(lambda response: 'q=Paciente' in response.url) as response:
            page.fill('#patientSearch', 'Paciente 05')
        self.assertEqual('true', response.value.request.headers.get('hx-request'))
        expect(page.locator('#patient-results .patient-mobile-row')).to_have_count(1)
        self.assertIn('1 paciente', page.inner_text('#patientResultCount'))
        self.assertIn('q=Paciente', page.url)
        self._assert_no_reload()

        page.fill('#patientSearch', '')
        expect(page.locator('#patient-results .patient-mobile-row')).to_have_count(20)
        page.click('#patient-results .pagination a:has-text("Próxima")')
        expect(page.locator('#patient-results')).to_contain_text('Página 2 de 2')
        self._assert_no_reload()

        row = page.locator('table.patients-table tbody tr').first
        row.locator('[data-bs-toggle="dropdown"]').click()
        self.assertEqual(1, row.locator('.dropdown-menu.show').count())
        page.once('dialog', lambda dialog: dialog.accept())
        with page.expect_navigation():
            row.locator('[data-delete-patient]').click()
        self.assertIn('26 pacientes', page.inner_text('#patientResultCount'))

    def test_agenda_navigation_status_and_refresh(self):
        page = self.page
        page.goto(f'{self.base}/agenda?view=week')
        self._mark_page()
        page.click('#agendaPeriodNext')
        expect(page.locator('#agendaApp')).to_contain_text('Semana Seguinte')
        self.assertEqual('agendaPeriodNext', page.evaluate('document.activeElement.id'))
        page.click('#agendaPeriodToday')
        expect(page.locator('#agendaApp')).to_contain_text('Semana Atual')
        page.click('[data-event-trigger] >> nth=0')
        page.wait_for_selector('#eventModal.show')
        page.check('input[name="eventStatus"][value="REALIZADA"]', force=True)
        with page.expect_response('**/agenda/events/status') as status:
            page.click('#saveEventStatus')
        self.assertEqual(200, status.value.status)
        page.wait_for_selector('.agenda-row.status-realizada')
        page.wait_for_selector('#eventModal', state='hidden')
        with page.expect_response('**/agenda/cache/refresh') as refresh:
            page.click('#refreshAgendaButton')
        self.assertEqual(200, refresh.value.status)
        page.click('#agendaViewMonth')
        page.wait_for_selector('.month-grid')
        self._assert_no_reload()

    def test_shell_sidebar_and_mobile_menu(self):
        page = self.page
        page.goto(f'{self.base}/index')
        self.assertFalse(page.evaluate('!!window.bootstrap'))
        page.click('#sidebarPinToggle')
        self.assertTrue(page.evaluate("document.body.classList.contains('sidebar-collapsed')"))
        self.assertEqual('0', page.evaluate("localStorage.getItem('sidebarPinned')"))
        self.assertTrue(page.locator('#sidebarPinToggle .lucide-chevrons-right').is_visible())
        page.click('#sidebarPinToggle')
        page.set_viewport_size({'width': 390, 'height': 800})
        page.reload()
        page.click('#menuToggle')
        self.assertEqual('true', page.get_attribute('#menuToggle', 'aria-expanded'))
        page.keyboard.press('Escape')
        self.assertEqual('false', page.get_attribute('#menuToggle', 'aria-expanded'))

    def test_settings_alpine_access_source(self):
        page = self.page
        page.goto(f'{self.base}/configuracoes/')
        form = page.locator('form[x-data="accessSource"]').first
        self.assertTrue(form.locator('fieldset.access-network-fields').is_visible())
        form.locator('input[value="local"]').check()
        expect(form.locator('fieldset.access-network-fields input[name="access_host"]')).to_be_disabled()
        self.assertTrue(form.locator('fieldset.access-local-fields').is_visible())

    def test_every_page_respects_enforced_csp(self):
        pages = [
            '/index', '/patients/patient/new',
            f'/patients/patient/{self.patient_id}', f'/patients/patient/{self.patient_id}/edit',
            f'/patient/{self.patient_id}/surgery/request', f'/surgery/{self.surgery_id}/edit',
            f'/surgery/{self.surgery_id}/confirmation', '/configuracoes/procedimentos',
            '/register_user', '/perfil', '/sincronizacao/historico', '/sincronizacao/configurar',
            '/change-password', '/patients/patient/999999',
        ]
        csp_headers = set()
        for url in pages:
            with self.subTest(url=url):
                response = self.page.goto(f'{self.base}{url}')
                csp_headers.add(response.headers.get('content-security-policy', ''))
                self.page.wait_for_load_state('load')
                if url.endswith('999999'):
                    # A própria página de erro responde 404 (esperado).
                    self.problems[:] = [msg for msg in self.problems if '404' not in msg]
                self.assertEqual([], self.problems, url)
        self.assertTrue(all("style-src 'self'" in header for header in csp_headers))
        # Prévia do PDF (iframe same-origin) continua permitida pela CSP.
        self.page.goto(f'{self.base}/surgery/{self.surgery_id}/confirmation')
        frame = self.page.locator('#pdfFrame')
        self.assertTrue(frame.get_attribute('src').endswith('/pdf/view'))
        # Tela de login (anônimo).
        anonymous = self.browser.new_context()
        login = anonymous.new_page()
        login.on('console', lambda message: self.problems.append(message.text)
                 if message.type == 'error' else None)
        login.goto(f'{self.base}/')
        login.wait_for_load_state('load')
        anonymous.close()

    def test_static_assets_are_compressed_and_cached(self):
        responses = []
        self.page.on('response', lambda response: responses.append(response)
                     if '/static/dist/' in response.url else None)
        self.page.goto(f'{self.base}/patients/patients')
        self.assertTrue(responses)
        for response in responses:
            with self.subTest(url=response.url):
                headers = response.headers
                self.assertEqual('gzip', headers.get('content-encoding'))
                self.assertIn('immutable', headers.get('cache-control', ''))


if __name__ == '__main__':
    unittest.main()
