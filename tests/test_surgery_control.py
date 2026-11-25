import os
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty, SpecialtySettings
from src.models.user import User
from src.services import access_surgery_service as svc
from src.services.access_local_copy import LocalCopyManager
from src.services.access_patient_service import (
    ACCESS_DRIVER, AccessConfig, AccessLookupError, AccessPatientService,
)

SURGERY_COLUMNS = ['prontuario', 'nome do paciente', 'dt_atend_cons', 'nome_medico_cons', 'especialidade_cons',
                   'procedimento_cir', 'dt_prov_CIR', 'orientacao_ss', 'CIRURGIA_agendada']
PROCEDURE_COLUMNS = ['codigo', 'nome']
SUSPENSION_COLUMNS = ['Nome_Paciente', 'Especialidade', 'Data_da_Cirurgia', 'Mot_Cancelam', 'Obs_Cancelam', 'Situaçao']
TODAY = date(2026, 11, 24)
WINDOW_START = datetime(2025, 11, 1)  # 12 meses antes do mês de TODAY


def surgery(prontuario, nome, programada, status, esp='Ortopedia', proc='0408050012', obs='', cadastro=None):
    return (prontuario, nome, cadastro or datetime(2026, 1, 5), 'DR. A', esp, proc, programada, obs, status)


class FakeCursor:
    def __init__(self, connection):
        self.connection, self.description, self._rows = connection, None, []

    def execute(self, sql, *params):
        connection = self.connection
        connection.executed.append((sql, params))
        if connection.gate is not None and 'WHERE 1=0' not in sql:
            connection.gate.wait(10)
        table = next(name for name in connection.tables if f'[{name}]' in sql)
        columns, rows = connection.tables[table]
        if table in connection.failing:
            raise RuntimeError('42S02', 'Could not find object')
        if 'WHERE 1=0' in sql:
            self.description = [(name, None, None, None, None, None, None) for name in columns]
            self._rows = []
            return
        selected = [col for col in columns if f'[{col}]' in sql.split(' FROM ')[0]]
        if table == 'Ocorrencias_SS':  # semântica SQL: NULL não satisfaz ">= ?"
            index = columns.index('dt_prov_CIR')
            if '[dt_prov_CIR] IS NULL' in sql:
                rows = [row for row in rows if row[index] is None]
            elif '[dt_prov_CIR] >= ?' in sql:
                rows = [row for row in rows if row[index] is not None]
        if connection.row_filter is not None:
            rows = [row for row in rows if connection.row_filter(table, columns, row, params)]
        self._rows = [tuple(row[columns.index(col)] for col in selected) for row in rows]

    def fetchmany(self, size):
        batch, self._rows = self._rows[:size], self._rows[size:]
        return batch

    def fetchall(self):
        rows, self._rows = self._rows, []
        return rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, tables, failing=(), gate=None, row_filter=None):
        self.tables, self.failing, self.executed = tables, set(failing), []
        self.gate, self.row_filter, self.closed = gate, row_filter, False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True

    def data_queries(self):
        return [(sql, params) for sql, params in self.executed if 'WHERE 1=0' not in sql]


def make_tables(surgeries, procedures=None, suspensions=None):
    return {
        'Ocorrencias_SS': (SURGERY_COLUMNS, surgeries),
        'tb_procedimentos_BC': (PROCEDURE_COLUMNS, procedures if procedures is not None else [('0408050012', 'Artrodese')]),
        'tb_registro_bC': (SUSPENSION_COLUMNS, suspensions or []),
    }


CONFIG = AccessConfig(host='srv', share_path='share', filename='db.accdb')


def patch_pyodbc(connection):
    fake = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
    return patch('src.services.access_patient_service.pyodbc', fake)


def new_service(patients=None, **kwargs):
    kwargs.setdefault('background', False)
    kwargs.setdefault('copy_manager', None)
    return svc.AccessSurgeryService(patients or AccessPatientService(), **kwargs)


def run_view(tables, failing=(), today=TODAY, **service_kwargs):
    connection = FakeConnection(tables, failing)
    service = new_service(**service_kwargs)
    with patch_pyodbc(connection):
        state = service.get_view(CONFIG, today)
    return state, connection, service


def load_with(tables, failing=()):
    state, connection, _ = run_view(tables, failing)
    return state.snapshot, connection


def wait_until(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


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
        self.assertEqual(date(2025, 11, 1), snapshot.covered_from)

    def test_null_and_invalid_dates_do_not_break(self):
        tables = make_tables([
            surgery(1, 'Ana', None, None),
            surgery(2, 'Bia', 'data ruim', None),
            surgery(3, 'Cris', datetime(2026, 11, 20), None, cadastro='lixo'),
        ])
        snapshot, _ = load_with(tables)
        undated = [row.paciente for row in snapshot.rows if row.sem_data]
        self.assertEqual(['Ana', 'Bia'], sorted(undated))
        self.assertEqual(1, len(svc.rows_in_period(snapshot.rows, date(2026, 11, 1), date(2026, 11, 30))))
        self.assertIsNone({r.paciente: r for r in snapshot.rows}['Cris'].cadastro)

    def test_suspension_linked_missing_ambiguous_and_divergent(self):
        day = datetime(2026, 11, 20)
        suspensions = [
            ('JOÃO da Silva', 'ortopedia', day, 'Paciente', 'Faltou', 'CANCELADA'),
            ('Maria  Souza', 'Ortopedia', day, 'Clínico', 'Febre', 'cancelada'),
            ('maria souza', 'ORTOPEDIA', day, 'Estrutura', 'Sem material', None),  # sem situação, com motivo
            ('Outro', 'Cardiologia', day, 'X', 'Y', 'CANCELADA'),
            ('Sem Motivo', 'Ortopedia', day, None, '', None),  # sem situação e sem motivo: ignorada
            ('Divergente', 'Ortopedia', day, None, None, 'REALIZADA'),
            ('Realizada Ok', 'Ortopedia', day, 'Lixo', 'Lixo', 'REALIZADA'),
        ]
        tables = make_tables([
            surgery(1, 'Joao da silva', day, 0),
            surgery(2, 'Maria Souza', day, 0),
            surgery(3, 'Sem Motivo', day, 0),  # só existe linha de registro sem motivo (ignorada)
            surgery(4, 'Realizada Ok', day, 1),
            surgery(5, 'Joao da silva', datetime(2026, 11, 21), 0),  # data diferente
            surgery(6, 'Divergente', day, 0),  # cancelada na agenda, realizada no registro
        ], suspensions=suspensions)
        snapshot, _ = load_with(tables)
        by_id = {row.prontuario: row for row in snapshot.rows}
        self.assertEqual(('confirmado', 'Paciente', 'Faltou'),
                         (by_id['1'].vinculo.estado, by_id['1'].vinculo.grupo, by_id['1'].vinculo.descricao))
        self.assertEqual('ambiguo', by_id['2'].vinculo.estado)
        self.assertEqual('', by_id['2'].vinculo.grupo)
        self.assertEqual('nao_localizado', by_id['3'].vinculo.estado)
        self.assertEqual('nao_localizado', by_id['5'].vinculo.estado)
        self.assertEqual('divergente', by_id['6'].vinculo.estado)
        self.assertIn('realizada', by_id['6'].vinculo.label)
        self.assertIsNone(by_id['4'].vinculo)
        summary = svc.suspension_summary(snapshot.rows)
        self.assertEqual(5, summary['total'])
        self.assertEqual((1, 2, 1), (summary['ambiguous'], summary['missing'], summary['divergent']))
        self.assertEqual([('Paciente', 1)], [(g['grupo'], g['count']) for g in summary['groups']])

    def test_registry_kind_uses_situacao_first(self):
        self.assertEqual('cancelada', svc.registry_kind('CANCELADA', '', ''))
        self.assertEqual('realizada', svc.registry_kind(' Realizada ', 'Motivo', 'Obs'))
        self.assertEqual('cancelada', svc.registry_kind(None, 'Motivo', ''))
        self.assertEqual('cancelada', svc.registry_kind('???', '', 'Obs'))
        self.assertEqual('', svc.registry_kind(None, None, ''))

    def test_registry_without_situacao_column_falls_back_to_motive(self):
        day = datetime(2026, 11, 20)
        tables = make_tables([surgery(1, 'Ana', day, 0)], suspensions=[('Ana', 'Ortopedia', day, 'Clínico', 'Febre', None)])
        tables['tb_registro_bC'] = (SUSPENSION_COLUMNS[:-1], [row[:-1] for row in tables['tb_registro_bC'][1]])
        snapshot, _ = load_with(tables)
        self.assertEqual('confirmado', snapshot.rows[0].vinculo.estado)

    def test_registry_table_unavailable_is_explicit(self):
        tables = make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), 0)])
        snapshot, _ = load_with(tables, failing={'tb_registro_bC'})
        self.assertEqual('indisponivel', snapshot.rows[0].vinculo.estado)
        self.assertTrue(any('tb_registro_bC' in w for w in snapshot.warnings))

    def test_procedure_table_unavailable_keeps_surgeries(self):
        tables = make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)])
        snapshot, _ = load_with(tables, failing={'tb_procedimentos_BC'})
        self.assertEqual(1, len(snapshot.rows))
        self.assertEqual('', snapshot.rows[0].procedimento_nome)
        self.assertTrue(snapshot.warnings)

    def test_missing_surgery_table_and_columns_become_guidance_without_paths(self):
        state, _, _ = run_view(make_tables([]), failing={'Ocorrencias_SS'})
        self.assertEqual('error', state.status)
        self.assertEqual('ACCESS_SURGERY_TABLE_NOT_FOUND', state.error['code'])
        tables = make_tables([])
        tables['Ocorrencias_SS'] = (['prontuario'], [])
        state, _, _ = run_view(tables)
        self.assertEqual('ACCESS_SURGERY_COLUMNS_MISSING', state.error['code'])
        self.assertNotIn('share', state.error['hint'])

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


class QueryShapeTests(unittest.TestCase):
    """As consultas devem ser filtradas e parametrizadas, nunca leituras de tabela inteira."""

    def test_every_data_query_is_filtered_and_parameterized(self):
        day = datetime(2026, 11, 20)
        tables = make_tables([surgery(1, 'Ana', day, 0)], suspensions=[('Ana', 'Ortopedia', day, 'M', 'D', 'CANCELADA')])
        _, connection, _ = run_view(tables)
        queries = connection.data_queries()
        self.assertEqual(4, len(queries))  # cirurgias, sem data, registro do bloco, procedimentos
        for sql, _params in queries:
            self.assertTrue(sql.startswith('SELECT '))
            self.assertIn(' WHERE ', sql)
        surgeries, undated, registry, procedures = queries
        self.assertIn("InStr(1, [especialidade_cons], 'ortop', 1) > 0", surgeries[0])
        self.assertIn('[dt_prov_CIR] >= ?', surgeries[0])
        self.assertEqual((WINDOW_START,), surgeries[1])
        self.assertIn('[dt_prov_CIR] IS NULL', undated[0])
        self.assertIn('[dt_atend_cons] >= ?', undated[0])
        self.assertEqual((WINDOW_START,), undated[1])
        self.assertIn('[Data_da_Cirurgia] >= ?', registry[0])
        self.assertIn("InStr(1, [Especialidade], 'ortop', 1) > 0", registry[0])
        self.assertEqual((WINDOW_START,), registry[1])
        self.assertIn('[codigo] IN (?)', procedures[0])
        self.assertEqual(('0408050012',), procedures[1])

    def test_procedures_use_in_batches_and_are_cached(self):
        rows = [surgery(i, f'P{i}', datetime(2026, 11, 20), None, proc=f'{i:010d}') for i in range(150)]
        tables = make_tables(rows, procedures=[(f'{i:010d}', f'Proc {i}') for i in range(150)])
        state, connection, service = run_view(tables)
        in_queries = [(sql, params) for sql, params in connection.data_queries() if ' IN (' in sql]
        self.assertEqual([100, 50], [len(params) for _, params in in_queries])
        self.assertEqual('Proc 7', {r.prontuario: r for r in state.snapshot.rows}['7'].procedimento_nome)
        with patch_pyodbc(connection):  # nova leitura: nomes vêm do cache de 24 h
            service.refresh(CONFIG, TODAY)
        self.assertEqual(2, len([1 for sql, _ in connection.data_queries() if ' IN (' in sql]))

    def test_row_cap_adds_warning(self):
        rows = [surgery(i, f'P{i}', datetime(2026, 11, 20), None) for i in range(30)]
        with patch.object(svc, 'MAX_ROWS', 10):
            state, _, _ = run_view(make_tables(rows))
        self.assertEqual(10, len([r for r in state.snapshot.rows if r.programada]))
        self.assertTrue(any('Limite' in w for w in state.snapshot.warnings))

    def test_history_months_comes_from_environment(self):
        with patch.dict(os.environ, {'SURGERY_HISTORY_MONTHS': '6'}):
            state, connection, _ = run_view(make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)]), history_months=None)
        self.assertEqual(date(2026, 5, 1), state.snapshot.covered_from)
        self.assertEqual((datetime(2026, 5, 1),), connection.data_queries()[0][1])


class LoaderBehaviourTests(unittest.TestCase):
    def test_get_view_returns_immediately_while_loading_and_runs_a_single_job(self):
        gate = threading.Event()
        connection = FakeConnection(make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)]), gate=gate)
        service = new_service(background=True)
        with patch_pyodbc(connection):
            began = time.monotonic()
            first = service.get_view(CONFIG, TODAY)
            second = service.get_view(CONFIG, TODAY)
            self.assertLess(time.monotonic() - began, 1.0)
            self.assertEqual(('loading', 'loading'), (first.status, second.status))
            self.assertIsNone(first.snapshot)
            self.assertTrue(wait_until(lambda: any('WHERE 1=0' not in sql for sql, _ in connection.executed)))
            gate.set()
            self.assertTrue(wait_until(lambda: service.get_view(CONFIG, TODAY).status == 'ready'))
        self.assertEqual(1, len([1 for sql, _ in connection.executed if 'FROM [Ocorrencias_SS] WHERE 1=0' in sql]))

    def test_shared_patient_lock_is_not_held_during_load(self):
        gate = threading.Event()
        connection = FakeConnection(make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)]), gate=gate)
        patients = AccessPatientService()
        service = new_service(patients, background=True)
        with patch_pyodbc(connection):
            service.get_view(CONFIG, TODAY)
            self.assertTrue(wait_until(lambda: any('WHERE 1=0' not in sql for sql, _ in connection.executed)))
            acquired = patients._lock.acquire(blocking=False)  # outras telas precisam do lock livre
            if acquired:
                patients._lock.release()
            gate.set()
            wait_until(lambda: service.get_view(CONFIG, TODAY).status == 'ready')
        self.assertTrue(acquired)

    def test_stale_snapshot_is_served_and_refreshed_in_background(self):
        now = [1000.0]
        connection = FakeConnection(make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)]))
        service = new_service(clock=lambda: now[0])
        with patch_pyodbc(connection):
            service.get_view(CONFIG, TODAY)
            loads = len([1 for sql, _ in connection.executed if 'Ocorrencias_SS] WHERE 1=0' in sql])
            now[0] += 100
            service.get_view(CONFIG, TODAY)  # ainda fresco
            self.assertEqual(loads, len([1 for sql, _ in connection.executed if 'Ocorrencias_SS] WHERE 1=0' in sql]))
            now[0] += 250  # passou de 5 min
            state = service.get_view(CONFIG, TODAY)
        self.assertEqual('ready', state.status)
        self.assertEqual(loads + 1, len([1 for sql, _ in connection.executed if 'Ocorrencias_SS] WHERE 1=0' in sql]))

    def test_failure_has_cooldown_and_manual_refresh_bypasses_it(self):
        now = [0.0]
        calls = []

        class Failing(AccessPatientService):
            @contextmanager
            def open_readonly(self, config, query_timeout=120):
                calls.append(1)
                raise AccessLookupError('ACCESS_QUERY_FAILED', 'Falhou.', 'Tente de novo.', 502)
                yield

        service = new_service(Failing(), clock=lambda: now[0])
        self.assertEqual('error', service.get_view(CONFIG, TODAY).status)
        now[0] += 10
        self.assertEqual('error', service.get_view(CONFIG, TODAY).status)
        self.assertEqual(1, len(calls))  # nenhuma nova tentativa em 30 s
        service.refresh(CONFIG, TODAY)  # pedido do usuário
        self.assertEqual(2, len(calls))
        now[0] += 40
        service.get_view(CONFIG, TODAY)
        self.assertEqual(3, len(calls))

    def test_stuck_load_is_discarded(self):
        now = [0.0]
        gate = threading.Event()
        connection = FakeConnection(make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)]), gate=gate)
        service = new_service(background=True, clock=lambda: now[0])
        with patch_pyodbc(connection):
            service.get_view(CONFIG, TODAY)
            self.assertTrue(wait_until(lambda: any('WHERE 1=0' not in sql for sql, _ in connection.executed)))
            now[0] += svc.STUCK_AFTER_SECONDS + 1
            state = service.get_view(CONFIG, TODAY)
            self.assertEqual('error', state.status)
            self.assertEqual('ACCESS_TIMEOUT', state.error['code'])
            gate.set()
            time.sleep(0.2)
            self.assertIsNone(service.get_view(CONFIG, TODAY).snapshot)  # resultado antigo descartado

    def test_config_change_resets_the_snapshot(self):
        connection = FakeConnection(make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)]))
        service = new_service()
        other = AccessConfig(host='outro', share_path='share', filename='db.accdb')
        with patch_pyodbc(connection):
            service.get_view(CONFIG, TODAY)
            first = len([1 for sql, _ in connection.executed if 'Ocorrencias_SS] WHERE 1=0' in sql])
            service.get_view(other, TODAY)
        self.assertEqual(first + 1, len([1 for sql, _ in connection.executed if 'Ocorrencias_SS] WHERE 1=0' in sql]))

    def test_ensure_range_loads_older_period_and_relinks_suspensions(self):
        old, recent = datetime(2025, 2, 10), datetime(2026, 11, 20)

        def only_in_range(table, columns, row, params):
            column = {'Ocorrencias_SS': 'dt_prov_CIR', 'tb_registro_bC': 'Data_da_Cirurgia'}.get(table)
            if column is None or not params or not isinstance(params[0], datetime):
                return True
            value = row[columns.index(column)]
            if value is None:
                return True
            return params[0] <= value and (len(params) < 2 or value < params[1])

        tables = make_tables(
            [surgery(1, 'Antiga', old, 0), surgery(2, 'Recente', recent, None)],
            suspensions=[('Antiga', 'Ortopedia', old, 'Clínico', 'Febre', 'CANCELADA')])
        connection = FakeConnection(tables, row_filter=only_in_range)
        service = new_service()
        with patch_pyodbc(connection):
            state = service.get_view(CONFIG, TODAY)
            self.assertEqual(['Recente'], [r.paciente for r in state.snapshot.rows])
            self.assertFalse(service.is_covered(date(2025, 2, 1)))
            state = service.ensure_range(CONFIG, date(2025, 2, 1))
        self.assertTrue(service.is_covered(date(2025, 2, 1)))
        by_name = {r.paciente: r for r in state.snapshot.rows}
        self.assertEqual({'Antiga', 'Recente'}, set(by_name))
        self.assertEqual(date(2024, 9, 1), state.snapshot.covered_from)
        self.assertEqual('confirmado', by_name['Antiga'].vinculo.estado)
        range_queries = [params for sql, params in connection.data_queries() if '[dt_prov_CIR] < ?' in sql]
        self.assertEqual([(datetime(2024, 9, 1), datetime(2025, 11, 1))], range_queries)

    def test_local_copy_is_used_and_falls_back_to_network(self):
        local = AccessConfig(host='', share_path='', filename='copia.accdb', source='local', local_path='C:\\cache\\copia.accdb')

        class Manager:
            def prepare(self, config, force=False):
                return local, None, {'copied': False, 'seconds': 0, 'megabytes': 1}

        opened = []

        class Flaky(AccessPatientService):
            def __init__(self, connection, fail_local):
                super().__init__()
                self.connection, self.fail_local = connection, fail_local

            @contextmanager
            def open_readonly(self, config, query_timeout=120):
                opened.append(config.source)
                if config.source == 'local' and self.fail_local:
                    raise AccessLookupError('ACCESS_QUERY_FAILED', 'x', 'y', 502)
                yield self.connection

        tables = make_tables([surgery(1, 'Ana', datetime(2026, 11, 20), None)])
        ok = new_service(Flaky(FakeConnection(tables), False), copy_manager=Manager()).get_view(CONFIG, TODAY)
        self.assertEqual(('cópia local', ['local']), (ok.snapshot.origin, opened))
        opened.clear()
        fallback = new_service(Flaky(FakeConnection(tables), True), copy_manager=Manager()).get_view(CONFIG, TODAY)
        self.assertEqual(['local', 'network'], opened)
        self.assertEqual('rede', fallback.snapshot.origin)
        self.assertTrue(any('cópia local' in w for w in fallback.snapshot.warnings))


class OpenReadonlyTests(unittest.TestCase):
    def test_dedicated_connection_is_closed_and_leaves_shared_state_alone(self):
        connection = FakeConnection(make_tables([]))
        patients = AccessPatientService()
        with patch_pyodbc(connection):
            with patients.open_readonly(CONFIG, query_timeout=30) as opened:
                self.assertIs(opened, connection)
                self.assertEqual(30, opened.timeout)
                self.assertTrue(patients._lock.acquire(blocking=False))  # lock compartilhado livre
                patients._lock.release()
        self.assertTrue(connection.closed)
        self.assertIsNone(patients._connection)

    def test_driver_errors_are_classified_and_connection_closed(self):
        connection = FakeConnection(make_tables([]))
        patients = AccessPatientService()
        with patch_pyodbc(connection), self.assertRaises(AccessLookupError) as ctx:
            with patients.open_readonly(CONFIG):
                raise RuntimeError('Permission denied')
        self.assertEqual('ACCESS_PERMISSION_DENIED', ctx.exception.code)
        self.assertTrue(connection.closed)

    def test_disabled_access_is_rejected_before_connecting(self):
        disabled = AccessConfig(host='srv', share_path='share', filename='db.accdb', enabled=False)
        with self.assertRaises(AccessLookupError) as ctx, patients_never_connect():
            with AccessPatientService().open_readonly(disabled):
                pass
        self.assertEqual('ACCESS_DISABLED', ctx.exception.code)


@contextmanager
def patients_never_connect():
    def boom(*args, **kwargs):
        raise AssertionError('não deveria conectar')
    with patch('src.services.access_patient_service.pyodbc', SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=boom)):
        yield


class LocalCopyManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'share' / 'db.accdb'
        self.source.parent.mkdir()
        self.source.write_bytes(b'A' * 4096)
        self.now = [1000.0]
        self.free = SimpleNamespace(free=10 ** 12)
        patcher = patch.object(AccessConfig, 'database_path', new_callable=PropertyMock, return_value=str(self.source))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.manager = LocalCopyManager(self.root / 'cache', enabled=True, max_mb=1, min_interval=600,
                                        clock=lambda: self.now[0], disk_usage=lambda path: self.free)

    def tearDown(self):
        self.tmp.cleanup()

    def prepare(self, force=False, config=CONFIG):
        return self.manager.prepare(config, force=force)

    def test_copies_once_and_returns_local_config(self):
        local, note, info = self.prepare()
        self.assertIsNone(note)
        self.assertTrue(info['copied'])
        self.assertEqual('local', local.source)
        self.assertEqual(b'A' * 4096, Path(local.local_path).read_bytes())
        self.assertEqual([], list((self.root / 'cache').glob('*.part')))
        self.assertEqual(b'A' * 4096, self.source.read_bytes())  # original intacto

    def test_unchanged_source_is_not_copied_again(self):
        self.prepare()
        _, _, info = self.prepare(force=True)
        self.assertFalse(info['copied'])

    def test_changed_source_waits_for_min_interval_unless_forced(self):
        self.prepare()
        self.source.write_bytes(b'B' * 8192)
        os.utime(self.source, (2_000_000_000, 2_000_000_000))
        self.now[0] += 60
        local, _, info = self.prepare()
        self.assertFalse(info['copied'])
        self.assertEqual(b'A' * 4096, Path(local.local_path).read_bytes())
        self.now[0] += 700
        local, _, info = self.prepare()
        self.assertTrue(info['copied'])
        self.assertEqual(b'B' * 8192, Path(local.local_path).read_bytes())
        self.source.write_bytes(b'C' * 100)
        os.utime(self.source, (2_100_000_000, 2_100_000_000))
        _, _, info = self.prepare(force=True)
        self.assertTrue(info['copied'])

    def test_skips_when_disabled_not_network_or_too_big(self):
        self.manager.enabled = False
        self.assertEqual((None, None), self.prepare()[:2])
        self.manager.enabled = True
        local_cfg = AccessConfig(host='', share_path='', filename='x.accdb', source='local', local_path='C:\\x.accdb')
        self.assertEqual((None, None), self.manager.prepare(local_cfg)[:2])
        self.source.write_bytes(b'A' * (2 * 1024 * 1024))
        result, note, _ = self.prepare()
        self.assertIsNone(result)
        self.assertIn('limite', note)

    def test_failures_fall_back_without_leaving_partial_files(self):
        self.free = SimpleNamespace(free=10)
        result, note, _ = self.prepare()
        self.assertIsNone(result)
        self.assertIn('Lendo direto pela rede', note)
        self.assertEqual([], list((self.root / 'cache').glob('*')))
        self.free = SimpleNamespace(free=10 ** 12)
        self.source.unlink()
        result, note, _ = self.prepare()
        self.assertIsNone(result)
        self.assertIn('rede', note)

    def test_keeps_previous_copy_when_refresh_fails(self):
        self.prepare()
        self.source.write_bytes(b'D' * 8192)
        os.utime(self.source, (2_200_000_000, 2_200_000_000))
        self.free = SimpleNamespace(free=10)
        local, note, _ = self.prepare(force=True)
        self.assertIsNotNone(local)
        self.assertIn('desatualizada', note)


class SurgeryControlRoutesTests(unittest.TestCase):
    PATHS = ('/controle-cirurgias/', '/controle-cirurgias/dia/2026-11-24')

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
            INSTANCE_PATH = Path(self.tmp.name) / 'instance'
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
        self.service = svc.access_surgery_service
        self.service.invalidate()

    def tearDown(self):
        self.service.invalidate()
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
        return svc.SurgerySnapshot(tuple(rows), ('Aviso de teste',), datetime(2026, 11, 24, 10, 0),
                                   date(2025, 11, 1), date(2025, 11, 1))

    @contextmanager
    def state(self, view_state, covered=True):
        with patch.object(self.service, 'get_view', return_value=view_state) as get_view, \
                patch.object(self.service, 'is_covered', return_value=covered), \
                patch.object(self.service, 'ensure_range', return_value=view_state) as ensure, \
                patch.object(self.service, 'refresh', return_value=view_state) as refresh:
            yield SimpleNamespace(get_view=get_view, ensure=ensure, refresh=refresh)

    def ready(self, rows=None, **kwargs):
        return svc.ViewState('ready', self.snapshot(rows), age=120.0, **kwargs)

    def get(self, path, **kwargs):
        return self.client.get(path, **kwargs).get_data(as_text=True)

    # -- autorização ------------------------------------------------------

    def test_anonymous_is_redirected_to_login(self):
        for path in self.PATHS:
            with self.subTest(path=path):
                self.assertEqual(302, self.client.get(path).status_code)
        self.assertEqual(302, self.client.post('/controle-cirurgias/atualizar').status_code)

    def test_non_admin_is_forbidden_including_htmx_and_never_touches_access(self):
        self.login(self.doctor_id)
        with self.state(self.ready()) as mocks:
            for path in self.PATHS:
                for headers in ({}, {'HX-Request': 'true'}):
                    with self.subTest(path=path, headers=headers):
                        self.assertEqual(403, self.client.get(path, headers=headers).status_code)
            self.assertEqual(403, self.client.post('/controle-cirurgias/atualizar').status_code)
            mocks.get_view.assert_not_called()
            mocks.refresh.assert_not_called()

    def test_navigation_link_only_for_admin(self):
        with self.state(self.ready()):
            self.login(self.admin_id)
            self.assertIn('/controle-cirurgias/', self.get('/controle-cirurgias/'))
            self.login(self.doctor_id)
            self.assertNotIn('/controle-cirurgias/', self.get('/'))

    def test_only_expected_methods_are_allowed(self):
        self.login(self.admin_id)
        for method in ('post', 'put', 'delete', 'patch'):
            self.assertEqual(405, getattr(self.client, method)('/controle-cirurgias/').status_code)
        self.assertEqual(405, self.client.get('/controle-cirurgias/atualizar').status_code)

    # -- estados ----------------------------------------------------------

    def test_loading_state_responds_without_waiting_and_polls(self):
        self.login(self.admin_id)
        loading = svc.ViewState('loading', None, 'Lendo cirurgias', 12.0, 'Carga inicial')
        with self.state(loading) as mocks:
            html = self.get('/controle-cirurgias/?date=2026-11-24')
        self.assertIn('Carregando as cirurgias do banco do CPAM', html)
        self.assertIn('Lendo cirurgias', html)
        self.assertIn('hx-trigger="every 2s"', html)
        self.assertIn('hx-get="/controle-cirurgias/?view=month&amp;date=2026-11-24"', html)
        mocks.ensure.assert_not_called()
        partial = self.get('/controle-cirurgias/?date=2026-11-24', headers={'HX-Request': 'true'})
        self.assertNotIn('<!DOCTYPE', partial)
        self.assertIn('id="scApp"', partial)

    def test_ready_state_stops_polling_and_shows_data(self):
        self.login(self.admin_id)
        with self.state(self.ready()):
            html = self.get('/controle-cirurgias/?view=month&date=2026-11-24')
        for text in ('Paciente Teste', 'Artrodese', '(0408050012)', 'Clínico', 'Febre alta', 'Obs importante',
                     'Novembro de 2026', 'Aviso de teste', 'sem data programada', 'Status desconhecido (9)',
                     'desde 11/2025', 'Atualizado às 10:00'):
            self.assertIn(text, html)
        self.assertNotIn('hx-trigger="every', html)

    def test_background_refresh_keeps_showing_old_data_and_polls(self):
        self.login(self.admin_id)
        view = svc.ViewState('loading', self.snapshot(), 'Lendo cirurgias', 3.0, 'Atualização', refreshing=True, age=400.0)
        with self.state(view):
            html = self.get('/controle-cirurgias/?date=2026-11-24')
        self.assertIn('Atualizando em segundo plano', html)
        self.assertIn('Paciente Teste', html)
        self.assertIn('hx-trigger="every 2s"', html)

    def test_error_state_has_guidance_retry_and_does_not_leak(self):
        self.login(self.admin_id)
        error = {'message': 'Microsoft Access Database Engine não está instalado.',
                 'hint': 'Instale o driver Access da mesma arquitetura do sistema.', 'code': 'ACCESS_DRIVER_MISSING'}
        with self.state(svc.ViewState('error', error=error)):
            response = self.client.get('/controle-cirurgias/')
        html = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn('Instale o driver Access', html)
        self.assertIn('Tentar novamente', html)
        self.assertNotIn('Traceback', html)
        self.assertNotIn('hx-trigger="every', html)

    def test_failed_refresh_keeps_old_data_with_warning(self):
        self.login(self.admin_id)
        view = self.ready(error={'message': 'Falhou.', 'hint': 'Tente de novo.', 'code': 'X'})
        with self.state(view):
            html = self.get('/controle-cirurgias/?date=2026-11-24')
        self.assertIn('Não foi possível atualizar: Falhou.', html)
        self.assertIn('Paciente Teste', html)

    def test_older_period_triggers_background_load_and_shows_panel(self):
        self.login(self.admin_id)
        loading = svc.ViewState('loading', self.snapshot(), 'Lendo cirurgias', 1.0, 'Período anterior', loading_range=True)
        with self.state(loading, covered=False) as mocks:
            html = self.get('/controle-cirurgias/?view=month&date=2024-03-10')
        mocks.ensure.assert_called_once()
        self.assertEqual(date(2024, 3, 1), mocks.ensure.call_args.args[1])
        self.assertIn('Carregando o período anterior', html)
        self.assertNotIn('Paciente Teste', html)

    # -- atualização manual ----------------------------------------------

    def test_refresh_post_triggers_background_refresh(self):
        self.login(self.admin_id)
        with self.state(self.ready()) as mocks:
            response = self.client.post('/controle-cirurgias/atualizar', data={'view': 'week', 'date': '2026-11-24'})
            self.assertEqual(303, response.status_code)
            self.assertIn('/controle-cirurgias/?view=week&date=2026-11-24', response.headers['Location'])
            htmx = self.client.post('/controle-cirurgias/atualizar', data={'view': 'month', 'date': '2026-11-24'},
                                    headers={'HX-Request': 'true'})
            self.assertEqual(200, htmx.status_code)
            self.assertNotIn('<!DOCTYPE', htmx.get_data(as_text=True))
        self.assertEqual(2, mocks.refresh.call_count)

    # -- lista, filtros, dia ----------------------------------------------

    def test_filters_week_view_and_invalid_params(self):
        self.login(self.admin_id)
        with self.state(self.ready()):
            week = self.get('/controle-cirurgias/?view=week&date=2026-11-25')
            self.assertIn('23/11/2026 a 29/11/2026', week)
            undated = self.get('/controle-cirurgias/?sem_data=1&date=2026-11-24')
            self.assertIn('Sem Data', undated)
            self.assertIn('fora do calendário', undated)
            canceled = self.get('/controle-cirurgias/?status=cancelada&date=2026-11-24')
            self.assertIn('Paciente Teste', canceled)
            self.assertNotIn('Status Estranho</td>', canceled)
            bad = self.client.get('/controle-cirurgias/?view=zzz&date=lixo&status=hack&q=' + 'x' * 500)
            self.assertEqual(200, bad.status_code)

    def test_empty_state(self):
        self.login(self.admin_id)
        with self.state(self.ready(rows=[])):
            html = self.get('/controle-cirurgias/')
        self.assertIn('Nenhuma cirurgia encontrada', html)

    def test_long_list_is_limited_with_notice(self):
        self.login(self.admin_id)
        rows = [svc.SurgeryRow(str(i), f'Paciente {i:03d}', None, '', 'Ortopedia', '', '', date(2026, 11, 24), '', 'sem_resposta', '')
                for i in range(350)]
        with self.state(self.ready(rows=rows)):
            html = self.get('/controle-cirurgias/?date=2026-11-24')
        self.assertIn('Exibindo as primeiras 300 de 350 cirurgias', html)

    def test_day_detail_reads_only_memory(self):
        self.login(self.admin_id)
        with self.state(self.ready()) as mocks:
            html = self.get('/controle-cirurgias/dia/2026-11-24', headers={'HX-Request': 'true'})
            self.assertIn('Paciente Teste', html)
            self.assertIn('Nenhuma cirurgia programada', self.get('/controle-cirurgias/dia/2026-11-10'))
            self.assertEqual(404, self.client.get('/controle-cirurgias/dia/xx').status_code)
            mocks.ensure.assert_not_called()
        with self.state(self.ready(), covered=False):
            self.assertIn('ainda não foi carregado', self.get('/controle-cirurgias/dia/2020-01-10'))
        with self.state(svc.ViewState('loading', None, 'Preparando')):
            self.assertIn('ainda estão sendo carregados', self.get('/controle-cirurgias/dia/2026-11-24'))


if __name__ == '__main__':
    unittest.main()
