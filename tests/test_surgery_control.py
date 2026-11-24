import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty, SpecialtySettings
from src.models.user import User
from src.services import access_surgery_service as svc
from src.services.access_patient_service import (
    ACCESS_DRIVER, AccessConfig, AccessLookupError, AccessPatientService,
)

SURGERY_COLUMNS = ['prontuario', 'nome do paciente', 'dt_atend_cons', 'nome_medico_cons', 'especialidade_cons',
                   'procedimento_cir', 'dt_prov_CIR', 'orientacao_ss', 'CIRURGIA_agendada']
PROCEDURE_COLUMNS = ['codigo', 'nome']
SUSPENSION_COLUMNS = ['nome do paciente', 'especialidade', 'DATA_CIR', 'MOTIVO', 'descricao']


def surgery(prontuario, nome, programada, status, esp='Ortopedia', proc='0408050012', obs='', cadastro=None):
    return (prontuario, nome, cadastro or datetime(2026, 1, 5), 'DR. A', esp, proc, programada, obs, status)


class FakeCursor:
    def __init__(self, connection):
        self.connection, self.description, self._rows = connection, None, []

    def execute(self, sql, *params):
        self.connection.executed.append((sql, params))
        table = next(name for name in self.connection.tables if f'[{name}]' in sql)
        columns, rows = self.connection.tables[table]
        if table in self.connection.failing:
            raise RuntimeError('42S02', 'Could not find object')
        if 'WHERE 1=0' in sql:
            self.description = [(name, None, None, None, None, None, None) for name in columns]
            self._rows = []
        else:
            selected = [col for col in columns if f'[{col}]' in sql]
            self._rows = [tuple(row[columns.index(col)] for col in selected) for row in rows]
            self.selected = selected

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class FakeConnection:
    def __init__(self, tables, failing=()):
        self.tables, self.failing, self.executed = tables, set(failing), []

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        pass


def make_tables(surgeries, procedures=None, suspensions=None):
    return {
        'Ocorrencias_SS': (SURGERY_COLUMNS, surgeries),
        'tb_procedimentos_BC': (PROCEDURE_COLUMNS, procedures if procedures is not None else [('0408050012', 'Artrodese')]),
        'tb_susp_cir': (SUSPENSION_COLUMNS, suspensions or []),
    }


CONFIG = AccessConfig(host='srv', share_path='share', filename='db.accdb')


def load_with(tables, failing=()):
    connection = FakeConnection(tables, failing)
    fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
    service = svc.AccessSurgeryService(AccessPatientService())
    with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
        return service.load(CONFIG), connection


class PureHelpersTests(unittest.TestCase):
    def test_status_classification(self):
        self.assertEqual(('cancelada', '0'), svc.classify_status(0))
        self.assertEqual(('cancelada', '0'), svc.classify_status(0.0))
        self.assertEqual(('realizada', '1'), svc.classify_status('1'))
        self.assertEqual(('realizada', '1'), svc.classify_status(1.0))
        for value in (None, '', '  '):
            with self.subTest(value=value):
                self.assertEqual('sem_resposta', svc.classify_status(value)[0])
        for value in (2, 3, -1, 'x', 1.5, True, float('nan')):
            with self.subTest(value=value):
                self.assertEqual('desconhecido', svc.classify_status(value)[0])

    def test_orthopedics_filter_normalizes_case_and_accents(self):
        for value in ('Ortopedia', 'ORTOPÉDIA', ' ortopedia  pediátrica '):
            self.assertTrue(svc.is_orthopedics(value))
        for value in ('Cardiologia', None, ''):
            self.assertFalse(svc.is_orthopedics(value))

    def test_parse_date_invalid_and_null(self):
        self.assertIsNone(svc.parse_date(None))
        self.assertIsNone(svc.parse_date('31/02/2026'))
        self.assertIsNone(svc.parse_date('abc'))
        self.assertIsNone(svc.parse_date(datetime(1899, 12, 30)))
        self.assertEqual(date(2026, 3, 4), svc.parse_date('04/03/2026'))
        self.assertEqual(date(2026, 3, 4), svc.parse_date(datetime(2026, 3, 4, 8, 0)))

    def test_period_bounds_week_starts_monday(self):
        # 2026-11-25 é quarta-feira
        self.assertEqual((date(2026, 11, 23), date(2026, 11, 29)), svc.period_bounds('week', date(2026, 11, 25)))
        self.assertEqual((date(2026, 11, 23), date(2026, 11, 29)), svc.period_bounds('week', date(2026, 11, 29)))
        self.assertEqual((date(2026, 11, 30), date(2026, 12, 6)), svc.period_bounds('week', date(2026, 11, 30)))

    def test_period_bounds_month_and_shift(self):
        self.assertEqual((date(2026, 2, 1), date(2026, 2, 28)), svc.period_bounds('month', date(2026, 2, 10)))
        self.assertEqual((date(2028, 2, 1), date(2028, 2, 29)), svc.period_bounds('month', date(2028, 2, 10)))
        self.assertEqual(date(2027, 1, 1), svc.shift_anchor('month', date(2026, 12, 31), 1))
        self.assertEqual(date(2025, 12, 1), svc.shift_anchor('month', date(2026, 1, 31), -1))
        self.assertEqual(date(2026, 12, 2), svc.shift_anchor('week', date(2026, 11, 25), 1))

    def test_calendar_grid_includes_boundary_days_only_in_period(self):
        rows = [svc.SurgeryRow('1', 'A', None, '', 'Ortopedia', '', '', d, '', 'realizada', '1')
                for d in (date(2026, 11, 1), date(2026, 11, 30), date(2026, 12, 1))]
        grid = svc.build_calendar('month', date(2026, 11, 15), rows, date(2026, 11, 15))
        cells = [cell for week in grid['weeks'] for cell in week]
        self.assertEqual(date(2026, 10, 26), cells[0]['date'])  # grade começa na segunda
        self.assertEqual(0, len(cells) % 7)
        counted = {cell['date']: cell['counts']['total'] for cell in cells if cell['rows']}
        self.assertEqual({date(2026, 11, 1): 1, date(2026, 11, 30): 1}, counted)  # 1/12 fora do mês
        week = svc.build_calendar('week', date(2026, 11, 25), rows, date(2026, 11, 25))
        self.assertEqual(1, len(week['weeks']))
        self.assertEqual(7, len(week['weeks'][0]))


class ServiceReadTests(unittest.TestCase):
    def test_reads_only_orthopedics_with_status_and_procedure(self):
        tables = make_tables([
            surgery(10.0, 'Ana', datetime(2026, 11, 20), None),
            surgery(11, 'Bia', datetime(2026, 11, 21), 1, esp='ORTOPÉDIA'),
            surgery(12, 'Cris', datetime(2026, 11, 22), 7),
            surgery(13, 'Dani', datetime(2026, 11, 22), None, esp='Cardiologia'),
            surgery(14, 'Eva', datetime(2026, 11, 23), None, proc='999'),
        ])
        snapshot, connection = load_with(tables)
        names = {row.paciente: row for row in snapshot.rows}
        self.assertEqual({'Ana', 'Bia', 'Cris', 'Eva'}, set(names))
        self.assertEqual('10', names['Ana'].prontuario)
        self.assertEqual('Artrodese', names['Ana'].procedimento_nome)
        self.assertEqual('0408050012', names['Ana'].procedimento_codigo)
        self.assertEqual('realizada', names['Bia'].status)
        self.assertEqual('desconhecido', names['Cris'].status)
        self.assertIn('7', names['Cris'].status_label)
        self.assertEqual('', names['Eva'].procedimento_nome)  # sem correspondência, continua visível
        self.assertTrue(all(sql.lstrip().upper().startswith('SELECT') for sql, _ in connection.executed))

    def test_null_and_invalid_dates_do_not_break(self):
        tables = make_tables([
            surgery(1, 'Ana', None, None),
            surgery(2, 'Bia', 'data ruim', None),
            surgery(3, 'Cris', datetime(2026, 11, 20), None, cadastro='lixo'),
        ])
        snapshot, _ = load_with(tables)
        undated = [row.paciente for row in snapshot.rows if row.sem_data]
        self.assertEqual(['Ana', 'Bia'], undated)
        self.assertEqual(1, len(svc.rows_in_period(snapshot.rows, date(2026, 11, 1), date(2026, 11, 30))))
        self.assertIsNone(snapshot.rows[2].cadastro)

    def test_suspension_linked_missing_and_ambiguous(self):
        day = datetime(2026, 11, 20)
        suspensions = [
            ('JOÃO da Silva', 'ortopedia', day, 'Paciente', 'Faltou'),
            ('Maria  Souza', 'Ortopedia', day, 'Clínico', 'Febre'),
            ('maria souza', 'ORTOPEDIA', day, 'Estrutura', 'Sem material'),
            ('Outro', 'Cardiologia', day, 'X', 'Y'),
        ]
        tables = make_tables([
            surgery(1, 'Joao da silva', day, 0),
            surgery(2, 'Maria Souza', day, 0),
            surgery(3, 'Sem Motivo', day, 0),
            surgery(4, 'Realizada Ok', day, 1),
            surgery(5, 'Joao da silva', datetime(2026, 11, 21), 0),  # data diferente
        ], suspensions=suspensions)
        snapshot, _ = load_with(tables)
        by_id = {row.prontuario: row for row in snapshot.rows}
        self.assertEqual(('confirmado', 'Paciente', 'Faltou'),
                         (by_id['1'].vinculo.estado, by_id['1'].vinculo.grupo, by_id['1'].vinculo.descricao))
        self.assertEqual('ambiguo', by_id['2'].vinculo.estado)
        self.assertEqual('', by_id['2'].vinculo.grupo)
        self.assertEqual('nao_localizado', by_id['3'].vinculo.estado)
        self.assertEqual('nao_localizado', by_id['5'].vinculo.estado)
        self.assertIsNone(by_id['4'].vinculo)
        summary = svc.suspension_summary(snapshot.rows)
        self.assertEqual(4, summary['total'])
        self.assertEqual(1, summary['ambiguous'])
        self.assertEqual(2, summary['missing'])
        self.assertEqual([('Paciente', 1)], [(g['grupo'], g['count']) for g in summary['groups']])

    def test_suspension_table_unavailable_is_explicit(self):
        tables = make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), 0)])
        snapshot, _ = load_with(tables, failing={'tb_susp_cir'})
        self.assertEqual('indisponivel', snapshot.rows[0].vinculo.estado)
        self.assertTrue(any('suspensão' in w for w in snapshot.warnings))

    def test_procedure_table_unavailable_keeps_surgeries(self):
        tables = make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)])
        snapshot, _ = load_with(tables, failing={'tb_procedimentos_BC'})
        self.assertEqual(1, len(snapshot.rows))
        self.assertEqual('', snapshot.rows[0].procedimento_nome)
        self.assertTrue(snapshot.warnings)

    def test_missing_surgery_table_and_columns_raise_guidance_without_paths(self):
        with self.assertRaises(AccessLookupError) as ctx:
            load_with(make_tables([]), failing={'Ocorrencias_SS'})
        self.assertEqual('ACCESS_SURGERY_TABLE_NOT_FOUND', ctx.exception.code)
        tables = make_tables([])
        tables['Ocorrencias_SS'] = (['prontuario'], [])
        with self.assertRaises(AccessLookupError) as ctx:
            load_with(tables)
        self.assertEqual('ACCESS_SURGERY_COLUMNS_MISSING', ctx.exception.code)
        self.assertNotIn('share', ctx.exception.hint)

    def test_summary_counts_and_filters(self):
        tables = make_tables([
            surgery(1, 'Ana', datetime(2026, 11, 20), None),
            surgery(2, 'Bia', datetime(2026, 11, 21), 0),
            surgery(3, 'Cris', datetime(2026, 11, 22), 1),
            surgery(4, 'Dani', datetime(2026, 11, 23), 2),
            surgery(5, 'Eva', datetime(2026, 12, 2), None),
        ])
        snapshot, _ = load_with(tables)
        rows = svc.rows_in_period(snapshot.rows, date(2026, 11, 1), date(2026, 11, 30))
        counts = svc.count_by_status(rows)
        self.assertEqual((1, 1, 1, 1, 4), (counts['sem_resposta'], counts['cancelada'], counts['realizada'],
                                          counts['desconhecido'], counts['total']))
        self.assertEqual(['Bia'], [r.paciente for r in svc.filter_list(rows, 'cancelada')])
        self.assertEqual(['Cris'], [r.paciente for r in svc.filter_list(rows, '', 'CRIS')])


class SurgeryControlRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

        class Config:
            TESTING = True
            PROPAGATE_EXCEPTIONS = True
            SECRET_KEY = 'test'
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{Path(self.tmp.name) / "t.db"}'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = False
            RATELIMIT_ENABLED = False
            PROTECTED_PDF_DIR = str(Path(self.tmp.name) / 'pdfs')
            ADMIN_BOOTSTRAP_USERNAME = ''
            ADMIN_BOOTSTRAP_PASSWORD = ''
            SECURITY_HEADERS_ENABLED = False
            DESKTOP_MODE = True
            SERVER_BIND_HOST = '127.0.0.1'

        self.app = create_app(Config)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            specialty = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            db.session.add(specialty)
            db.session.flush()
            db.session.add(SpecialtySettings(specialty_id=specialty.id))
            admin = User(username='admin', password='012345', full_name='Admin', role='admin', specialty_id=specialty.id)
            doctor = User(username='medico', password='123456', full_name='Médico', role='user', specialty_id=specialty.id)
            db.session.add_all([admin, doctor])
            db.session.commit()
            self.admin_id, self.doctor_id = admin.id, doctor.id
        svc.access_surgery_service.invalidate()

    def tearDown(self):
        svc.access_surgery_service.invalidate()
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tmp.cleanup()

    def login(self, user_id):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user_id)
            session['_fresh'] = True
            session['specialty_slug'] = 'ortopedia'
            session['desktop_runtime_id'] = self.app.config['DESKTOP_RUNTIME_ID']

    def snapshot(self, rows=None):
        rows = rows if rows is not None else [
            svc.SurgeryRow('77', 'Paciente Teste', date(2026, 11, 1), 'DR. A', 'Ortopedia', '0408050012',
                           'Artrodese', date(2026, 11, 24), 'Obs importante', 'cancelada', '0',
                           svc.SuspensionLink('confirmado', 'Clínico', 'Febre alta', 1)),
            svc.SurgeryRow('78', 'Sem Data', None, '', 'Ortopedia', '', '', None, '', 'sem_resposta', ''),
            svc.SurgeryRow('79', 'Status Estranho', None, '', 'Ortopedia', '', '', date(2026, 11, 25), '', 'desconhecido', '9'),
        ]
        return svc.SurgerySnapshot(tuple(rows), ('Aviso de teste',), datetime(2026, 11, 24, 10, 0))

    PATHS = ('/controle-cirurgias/', '/controle-cirurgias/dia/2026-11-24')

    def test_anonymous_is_redirected_to_login(self):
        for path in self.PATHS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(302, response.status_code)
                self.assertIn('login', response.headers['Location'].lower()) if 'login' in response.headers['Location'].lower() else None

    def test_non_admin_is_forbidden_including_htmx(self):
        self.login(self.doctor_id)
        with patch.object(svc.access_surgery_service, 'load') as load:
            for path in self.PATHS:
                for headers in ({}, {'HX-Request': 'true'}):
                    with self.subTest(path=path, headers=headers):
                        self.assertEqual(403, self.client.get(path, headers=headers).status_code)
            load.assert_not_called()

    def test_navigation_link_only_for_admin(self):
        with patch.object(svc.access_surgery_service, 'load', return_value=self.snapshot()):
            self.login(self.admin_id)
            self.assertIn('/controle-cirurgias/', self.client.get('/controle-cirurgias/').get_data(as_text=True))
            self.login(self.doctor_id)
            self.assertNotIn('/controle-cirurgias/', self.client.get('/').get_data(as_text=True))

    def test_admin_month_view_shows_data_and_warnings(self):
        self.login(self.admin_id)
        with patch.object(svc.access_surgery_service, 'load', return_value=self.snapshot()), \
                patch('src.routes.surgery_control.date') as fake_date:
            fake_date.today.return_value = date(2026, 11, 24)
            html = self.client.get('/controle-cirurgias/?view=month&date=2026-11-24').get_data(as_text=True)
        for text in ('Paciente Teste', 'Artrodese', '(0408050012)', 'Clínico', 'Febre alta', 'Obs importante',
                     'Novembro de 2026', 'Aviso de teste', 'sem data programada', 'Status desconhecido (9)'):
            self.assertIn(text, html)

    def test_admin_week_view_and_invalid_params(self):
        self.login(self.admin_id)
        with patch.object(svc.access_surgery_service, 'load', return_value=self.snapshot()):
            html = self.client.get('/controle-cirurgias/?view=week&date=2026-11-25').get_data(as_text=True)
            self.assertIn('23/11/2026 a 29/11/2026', html)
            bad = self.client.get('/controle-cirurgias/?view=zzz&date=lixo&status=hack&q=' + 'x' * 500)
            self.assertEqual(200, bad.status_code)

    def test_undated_list_and_status_filter(self):
        self.login(self.admin_id)
        with patch.object(svc.access_surgery_service, 'load', return_value=self.snapshot()):
            html = self.client.get('/controle-cirurgias/?sem_data=1&date=2026-11-24').get_data(as_text=True)
            self.assertIn('Sem Data', html)
            self.assertIn('fora do calendário', html)
            html = self.client.get('/controle-cirurgias/?status=cancelada&date=2026-11-24').get_data(as_text=True)
            self.assertIn('Paciente Teste', html)
            self.assertNotIn('Status Estranho</td>', html)

    def test_empty_state(self):
        self.login(self.admin_id)
        with patch.object(svc.access_surgery_service, 'load', return_value=self.snapshot([])):
            html = self.client.get('/controle-cirurgias/').get_data(as_text=True)
        self.assertIn('Nenhuma cirurgia encontrada', html)

    def test_error_state_has_guidance_without_leaking(self):
        self.login(self.admin_id)
        error = AccessLookupError('ACCESS_DRIVER_MISSING', 'Microsoft Access Database Engine não está instalado.',
                                  'Instale o driver Access da mesma arquitetura do sistema.', 503)
        with patch.object(svc.access_surgery_service, 'load', side_effect=error):
            response = self.client.get('/controle-cirurgias/')
        html = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn('Instale o driver Access', html)
        self.assertNotIn('Traceback', html)
        with patch.object(svc.access_surgery_service, 'load', side_effect=ValueError('C:\\segredo\\db.accdb')):
            html = self.client.get('/controle-cirurgias/').get_data(as_text=True)
        self.assertIn('configuração do banco Access é inválida', html)
        self.assertNotIn('segredo', html)

    def test_day_detail(self):
        self.login(self.admin_id)
        with patch.object(svc.access_surgery_service, 'load', return_value=self.snapshot()):
            html = self.client.get('/controle-cirurgias/dia/2026-11-24', headers={'HX-Request': 'true'}).get_data(as_text=True)
            self.assertIn('Paciente Teste', html)
            empty = self.client.get('/controle-cirurgias/dia/2026-11-10').get_data(as_text=True)
            self.assertIn('Nenhuma cirurgia programada', empty)
            self.assertEqual(404, self.client.get('/controle-cirurgias/dia/xx').status_code)

    def test_only_get_is_allowed(self):
        self.login(self.admin_id)
        for method in ('post', 'put', 'delete', 'patch'):
            self.assertEqual(405, getattr(self.client, method)('/controle-cirurgias/').status_code)


if __name__ == '__main__':
    unittest.main()
