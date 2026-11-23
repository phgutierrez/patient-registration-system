import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from src.app import create_app
from src.extensions import db
from src.models.patient import Patient
from src.models.specialty import Specialty
from src.models.user import User
from src.routes.today import filter_doctor_schedule, patient_from_access
from src.services.access_patient_service import (
    AccessConfig, AccessPatientService, doctor_name_matches, normalize_person_name,
    normalize_turno,
)

CONFIG = AccessConfig('192.168.1.252', r'naqh\AMBULATORIO_SERV', 'AMBULATORIO_SERV.accdb')


class NameMatchingTests(unittest.TestCase):
    def test_normalizes_accents_titles_and_punctuation(self):
        self.assertEqual('joao da silva', normalize_person_name('Dr. João  da Silva'))

    def test_accepts_small_differences(self):
        self.assertTrue(doctor_name_matches('JOAO DA SILVA', 'Dr. João Silva'))
        self.assertTrue(doctor_name_matches('Maria Aparecida Souza', 'Maria Aparecida Sousa'))
        self.assertTrue(doctor_name_matches('Pedro Henrique Freitas', 'Pedro Freitas'))
        self.assertTrue(doctor_name_matches('dra. ana  beatriz lima', 'Ana Beatriz Lima'))

    def test_rejects_different_doctors(self):
        self.assertFalse(doctor_name_matches('Carlos Mendes', 'Pedro Freitas'))
        self.assertFalse(doctor_name_matches('Pedro Lima', 'Pedro Freitas'))
        self.assertFalse(doctor_name_matches('', 'Pedro Freitas'))

    def test_normalize_turno(self):
        self.assertEqual('MANHA', normalize_turno('MANHÃ'))
        self.assertEqual('MANHA', normalize_turno('manha'))
        self.assertEqual('TARDE', normalize_turno('TARDE'))
        self.assertEqual('', normalize_turno(None))


class ScheduleFilterTests(unittest.TestCase):
    rows = [
        {'prontuario': '3', 'nome': 'C', 'medico': 'PEDRO FREITAS', 'turno': 'TARDE', 'quandoreg': datetime(2026, 11, 23, 13, 0)},
        {'prontuario': '1', 'nome': 'A', 'medico': 'Pedro Freitas', 'turno': 'MANHA', 'quandoreg': datetime(2026, 11, 23, 7, 30)},
        {'prontuario': '2', 'nome': 'B', 'medico': 'Pedro Freitaz', 'turno': 'MANHA', 'quandoreg': datetime(2026, 11, 23, 7, 5)},
        {'prontuario': '4', 'nome': 'D', 'medico': 'Outro Medico', 'turno': 'MANHA', 'quandoreg': datetime(2026, 11, 23, 6, 0)},
        {'prontuario': '5', 'nome': 'E', 'medico': 'Pedro Freitas', 'turno': 'MANHA', 'quandoreg': None},
    ]

    def test_orders_by_quandoreg_and_numbers_positions(self):
        mine, items = filter_doctor_schedule(self.rows, 'Pedro Freitas', 'ambos')
        self.assertEqual(4, len(mine))
        self.assertEqual(['2', '1', '3', '5'], [item['prontuario'] for item in items])
        self.assertEqual([1, 2, 3, 4], [item['posicao'] for item in items])

    def test_filters_by_turno(self):
        _, manha = filter_doctor_schedule(self.rows, 'Pedro Freitas', 'manha')
        _, tarde = filter_doctor_schedule(self.rows, 'Pedro Freitas', 'tarde')
        self.assertEqual(['2', '1', '5'], [item['prontuario'] for item in manha])
        self.assertEqual(['3'], [item['prontuario'] for item in tarde])
        self.assertEqual(1, tarde[0]['posicao'])


class PatientFromAccessTests(unittest.TestCase):
    def test_converts_access_record(self):
        values = patient_from_access({
            'nome': 'Paciente Teste', 'data_nascimento': datetime(2015, 3, 4), 'sexo': 'FEMININO',
            'nome_mae': 'Mae', 'cns': '123 4567 8901 2345', 'cidade': 'Fortaleza', 'contato': '85 99999-9999',
        }, '777', 1)
        self.assertEqual('F', values['sexo'])
        self.assertEqual('123456789012345', values['cns'])
        self.assertEqual(datetime(2015, 3, 4), values['data_nascimento'])
        self.assertEqual('', values['diagnostico'])
        self.assertEqual('777', values['prontuario'])

    def test_accepts_text_dates_and_rejects_incomplete(self):
        self.assertEqual(datetime(2010, 1, 2), patient_from_access({'nome': 'X', 'data_nascimento': '02/01/2010'}, '1')['data_nascimento'])
        self.assertEqual(datetime(2010, 1, 2), patient_from_access({'nome': 'X', 'data_nascimento': '2010-01-02 00:00:00'}, '1')['data_nascimento'])
        self.assertIsNone(patient_from_access({'nome': '', 'data_nascimento': '02/01/2010'}, '1'))
        self.assertIsNone(patient_from_access({'nome': 'X', 'data_nascimento': None}, '1'))


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = None
        self._rows = []

    def execute(self, sql, *params):
        self.connection.executions.append((sql, params))
        if 'WHERE 1=0' in sql:
            columns = self.connection.occ_columns if '[Ocorrencias]' in sql else self.connection.patient_columns
            self.description = [(name, None, None, None, None, None, None) for name in columns]
        elif '[Ocorrencias]' in sql:
            self._rows = list(self.connection.occ_rows)
        else:
            self._rows = [row for row in self.connection.names if row[0] in params]
        return self

    def fetchall(self):
        return self._rows

    def close(self):
        pass


class FakeConnection:
    occ_columns = ['ID', 'DT_ATEND', 'Nome_medico', 'turnomed', 'QUANDOREG', 'Prontuario']
    patient_columns = ['Prontuario', 'Nome do Paciente']

    def __init__(self):
        self.executions = []
        self.occ_rows = [
            # Ordem do SELECT: dt_atend, medico, turno, quandoreg, prontuario
            (datetime(2026, 11, 23), 'PEDRO FREITAS', 'MANHÃ', datetime(2026, 11, 23, 7, 0), 101.0),
            (datetime(2026, 11, 23), 'PEDRO FREITAS', 'TARDE', datetime(2026, 11, 23, 12, 0), '102'),
        ]
        self.names = [('101', 'Ana Souza')]

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        pass


class DailyAppointmentsServiceTests(unittest.TestCase):
    def setUp(self):
        self.now = [0.0]
        self.service = AccessPatientService(clock=lambda: self.now[0])
        self.connection = FakeConnection()
        self.connect = patch.object(AccessPatientService, '_connect', side_effect=lambda config: self._open())
        self.connect.start()

    def tearDown(self):
        self.connect.stop()

    def _open(self):
        self.service._connection = self.connection
        return self.connection

    def test_queries_day_range_and_matches_names(self):
        result = self.service.daily_appointments(CONFIG, date(2026, 11, 23))
        occ_sql, params = next(item for item in self.connection.executions if '[DT_ATEND] >= ?' in item[0])
        self.assertIn('[DT_ATEND] < ?', occ_sql)
        self.assertEqual((datetime(2026, 11, 23), datetime(2026, 11, 24)), params)
        rows = {row['prontuario']: row for row in result['rows']}
        self.assertEqual('Ana Souza', rows['101']['nome'])
        self.assertEqual('Prontuário 102', rows['102']['nome'])
        self.assertEqual('MANHA', rows['101']['turno'])
        self.assertTrue(any(' IN (?, ?)' in sql for sql, _ in self.connection.executions))

    def test_cache_lasts_three_minutes_and_force_bypasses(self):
        self.service.daily_appointments(CONFIG, date(2026, 11, 23))
        count = len(self.connection.executions)
        self.now[0] = 179
        self.assertEqual('memory_cache', self.service.daily_appointments(CONFIG, date(2026, 11, 23))['source'])
        self.assertEqual(count, len(self.connection.executions))
        self.assertEqual('access', self.service.daily_appointments(CONFIG, date(2026, 11, 23), force=True)['source'])
        self.now[0] = 1000
        self.assertEqual('access', self.service.daily_appointments(CONFIG, date(2026, 11, 23))['source'])


def _config(root: Path):
    database = root / 'instance' / 'today.db'
    database.parent.mkdir(parents=True, exist_ok=True)
    return type('TodayConfig', (), {
        'TESTING': True, 'SECRET_KEY': 'today-test-secret-key', 'BASE_DIR': root,
        'INSTANCE_PATH': database.parent, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False, 'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': False, 'PROTECTED_PDF_DIR': root / 'pdfs',
        'ADMIN_BOOTSTRAP_USERNAME': '', 'ADMIN_BOOTSTRAP_PASSWORD': '',
        'SECURITY_HEADERS_ENABLED': False, 'DESKTOP_MODE': False, 'SYNC_ENABLED': False,
    })


class TodayRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.app = create_app(_config(Path(self.tempdir.name)))
        with self.app.app_context():
            db.create_all()
            specialty = Specialty(slug='ortopedia', name='Ortopedia', is_active=True)
            db.session.add(specialty)
            db.session.flush()
            user = User(username='pedro', password='012345', full_name='Pedro Freitas', specialty_id=specialty.id)
            db.session.add(user)
            db.session.add(Patient(
                nome='Paciente Local', prontuario='500', data_nascimento=datetime(1990, 1, 1), sexo='M',
                nome_mae='Mae', cns='1', cidade='Fortaleza', contato='1', diagnostico='Gonartrose',
                cid='M17', specialty_id=specialty.id,
            ))
            db.session.commit()
            self.user_id, self.specialty_id = user.id, specialty.id
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session['_user_id'] = str(self.user_id)
            session['_fresh'] = True
            session['specialty_slug'] = 'ortopedia'
            session['desktop_runtime_id'] = self.app.config['DESKTOP_RUNTIME_ID']

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def test_lists_only_logged_doctor_in_order(self):
        rows = [
            {'prontuario': '2', 'nome': 'Segundo', 'medico': 'PEDRO FREITAS', 'turno': 'MANHA', 'quandoreg': datetime(2026, 11, 23, 8), 'dt_atend': None},
            {'prontuario': '1', 'nome': 'Primeiro', 'medico': 'Dr. Pedro Freitas', 'turno': 'MANHA', 'quandoreg': datetime(2026, 11, 23, 7), 'dt_atend': None},
            {'prontuario': '9', 'nome': 'Outro', 'medico': 'Carlos Mendes', 'turno': 'MANHA', 'quandoreg': datetime(2026, 11, 23, 6), 'dt_atend': None},
        ]
        with patch('src.routes.today.access_patient_service.daily_appointments',
                   return_value={'rows': rows, 'synced_at': datetime(2026, 11, 23, 9, 5), 'source': 'access'}) as daily:
            response = self.client.get('/hoje?turno=manha&sync=1', headers={'HX-Request': 'true'})
        html = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertTrue(daily.call_args.kwargs['force'])
        self.assertLess(html.index('Primeiro'), html.index('Segundo'))
        self.assertNotIn('Outro', html)
        self.assertIn('Atualizado às 09:05', html)
        self.assertIn('every 180s', html)

    def test_full_page_renders_modal_and_placeholder(self):
        with patch('src.routes.today.access_patient_service.daily_appointments',
                   return_value={'rows': [], 'synced_at': datetime.now(), 'source': 'access'}):
            html = self.client.get('/hoje').get_data(as_text=True)
        self.assertIn('todayPatientModal', html)
        self.assertIn('ainda não está disponível', html)

    def test_request_surgery_reuses_existing_patient(self):
        with patch('src.routes.today.access_patient_service.search') as search:
            response = self.client.post('/hoje/solicitar-cirurgia', data={'prontuario': '500'})
        search.assert_not_called()
        self.assertEqual(302, response.status_code)
        self.assertIn('/surgery/request', response.headers['Location'])

    def test_request_surgery_imports_patient_from_access(self):
        data = {'nome': 'Novo Paciente', 'data_nascimento': datetime(2012, 5, 6), 'sexo': 'F',
                'nome_mae': 'Mae', 'cns': '700000000000001', 'cidade': 'Caucaia', 'contato': '85988887777'}
        with patch('src.routes.today.access_patient_service.search',
                   return_value={'found': True, 'data': data, 'source': 'access'}):
            response = self.client.post('/hoje/solicitar-cirurgia', data={'prontuario': '900'})
        self.assertEqual(302, response.status_code)
        with self.app.app_context():
            patient = Patient.query.filter_by(prontuario='900').one()
            self.assertEqual('Novo Paciente', patient.nome)
            self.assertEqual(self.specialty_id, patient.specialty_id)
            self.assertTrue(response.headers['Location'].endswith(f'/patient/{patient.id}/surgery/request'))
            patient_id = patient.id
        page = self.client.get(f'/patient/{patient_id}/surgery/request').get_data(as_text=True)
        self.assertIn('Novo Paciente', page)
        self.assertIn('complete <strong>diagnóstico</strong>', page)

    def test_request_surgery_not_found_in_access(self):
        with patch('src.routes.today.access_patient_service.search',
                   return_value={'found': False, 'data': None, 'source': 'access'}):
            response = self.client.post('/hoje/solicitar-cirurgia', data={'prontuario': '901'})
        self.assertEqual(302, response.status_code)
        self.assertIn('/hoje', response.headers['Location'])
        with self.app.app_context():
            self.assertIsNone(Patient.query.filter_by(prontuario='901').first())


if __name__ == '__main__':
    unittest.main()
