import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.services.access_patient_service import (
    ACCESS_DRIVER, AccessConfig, AccessLookupError, AccessPatientService,
    validate_access_config,
)


class FakeCursor:
    def __init__(self, columns=None, result=None, execute_error=None):
        self.description = None
        self.columns_for_description = columns
        self.result = result
        self.execute_error = execute_error
        self.executions = []
        self.closed = False

    def execute(self, sql, parameter=None):
        if self.execute_error:
            raise self.execute_error
        self.executions.append((sql, parameter))
        if 'WHERE 1=0' in sql:
            self.description = [
                (name, None, None, None, None, None, None)
                for name in (self.columns_for_description or [])
            ]
        return self

    def fetchone(self):
        return self.result

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, columns, result, schema_error=None):
        self.schema_cursor = FakeCursor(columns=columns, execute_error=schema_error)
        self.query_cursor = FakeCursor(result=result)
        self.cursor_calls = 0
        self.closed = False

    def cursor(self):
        self.cursor_calls += 1
        return self.schema_cursor if self.cursor_calls == 1 else self.query_cursor

    def close(self):
        self.closed = True


class AccessConfigurationTests(unittest.TestCase):
    def test_builds_safe_unc_path(self):
        config = AccessConfig('192.168.1.252', r'naqh\AMBULATORIO_SERV', 'AMBULATORIO_SERV.accdb')
        self.assertEqual(r'\\192.168.1.252\naqh\AMBULATORIO_SERV\AMBULATORIO_SERV.accdb', config.unc_path)

    def test_rejects_unsafe_or_invalid_paths(self):
        invalid = [
            AccessConfig('http://server', 'share', 'file.accdb'),
            AccessConfig('server', r'share\..\private', 'file.accdb'),
            AccessConfig('server', r'C:\data', 'file.accdb'),
            AccessConfig('server', 'share/path', 'file.accdb'),
            AccessConfig('server', 'share', r'dir\file.accdb'),
            AccessConfig('server', 'share', 'file.sqlite'),
        ]
        for config in invalid:
            with self.subTest(config=config), self.assertRaises(ValueError):
                validate_access_config(config)

    def test_accepts_existing_local_access_file_and_rejects_nonlocal_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            local_file = Path(temp_dir) / 'patients.accdb'
            local_file.touch()
            config = AccessConfig('', '', '', source='local', local_path=str(local_file))
            validate_access_config(config)
            self.assertEqual(str(local_file), config.database_path)

        invalid = [
            AccessConfig('', '', '', source='local', local_path='patients.accdb'),
            AccessConfig('', '', '', source='local', local_path=r'\\server\share\patients.accdb'),
            AccessConfig('', '', '', source='local', local_path=r'C:\data\patients.sqlite'),
            AccessConfig('', '', '', source='invalid', local_path=r'C:\data\patients.accdb'),
        ]
        for config in invalid:
            with self.subTest(config=config), self.assertRaises(ValueError):
                validate_access_config(config)


class AccessLookupTests(unittest.TestCase):
    def setUp(self):
        self.config = AccessConfig('server', 'share', 'patients.accdb')

    def test_missing_driver_has_specific_error(self):
        service = AccessPatientService()
        fake_pyodbc = SimpleNamespace(drivers=lambda: [], connect=lambda *args, **kwargs: None)
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            with self.assertRaises(AccessLookupError) as raised:
                service.search(self.config, '123')
        self.assertEqual('ACCESS_DRIVER_MISSING', raised.exception.code)

    def test_query_is_read_only_projected_parameterized_and_cached(self):
        columns = ['prontuario', 'nome do paciente', 'Telefone', 'campo_grande_nao_usado']
        connection = FakeConnection(columns, ('123', 'Paciente Teste', '9999'))
        calls = []
        fake_pyodbc = SimpleNamespace(
            drivers=lambda: [ACCESS_DRIVER],
            connect=lambda connection_string, **kwargs: calls.append((connection_string, kwargs)) or connection,
        )
        service = AccessPatientService()
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            first = service.search(self.config, '123')
            second = service.search(self.config, '123')
        self.assertTrue(first['found'])
        self.assertEqual('memory_cache', second['source'])
        self.assertEqual(1, len(calls))
        connection_string, kwargs = calls[0]
        self.assertIn('READONLY=TRUE', connection_string)
        self.assertTrue(kwargs['autocommit'])
        sql, parameter = connection.query_cursor.executions[0]
        self.assertIn('SELECT TOP 1', sql)
        self.assertNotIn('campo_grande_nao_usado', sql)
        self.assertNotIn('INSERT', sql.upper())
        self.assertEqual('123', parameter)
        schema_sql, schema_parameter = connection.schema_cursor.executions[0]
        self.assertEqual('SELECT * FROM [cadastro_de_pacientes] WHERE 1=0', schema_sql)
        self.assertIsNone(schema_parameter)
        self.assertTrue(connection.schema_cursor.closed)
        self.assertTrue(connection.query_cursor.closed)

    def test_local_source_uses_direct_file_and_readonly_connection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            local_file = Path(temp_dir) / 'patients.accdb'
            local_file.touch()
            config = AccessConfig('', '', '', source='local', local_path=str(local_file))
            connection = FakeConnection(['prontuario'], ('123',))
            calls = []
            fake_pyodbc = SimpleNamespace(
                drivers=lambda: [ACCESS_DRIVER],
                connect=lambda connection_string, **kwargs: calls.append(connection_string) or connection,
            )
            with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
                result = AccessPatientService().search(config, '123')
        self.assertTrue(result['found'])
        self.assertIn(f'DBQ={local_file}', calls[0])
        self.assertIn('READONLY=TRUE', calls[0])
        self.assertNotIn('\\\\server', calls[0])

    def test_missing_local_file_has_specific_error(self):
        config = AccessConfig('', '', '', source='local', local_path=r'C:\missing\patients.accdb')
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER])
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            with self.assertRaises(AccessLookupError) as raised:
                AccessPatientService().search(config, '123')
        self.assertEqual('ACCESS_FILE_NOT_FOUND', raised.exception.code)

    def test_schema_discovery_does_not_use_cursor_columns(self):
        class CursorWithoutColumns(FakeCursor):
            def columns(self, *args, **kwargs):
                raise AssertionError('cursor.columns() não deve ser usado')

        connection = FakeConnection(['prontuario', 'Nome do Paciente'], ('123', 'Teste'))
        connection.schema_cursor = CursorWithoutColumns(columns=['prontuario', 'Nome do Paciente'])
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            result = AccessPatientService().search(self.config, '123')
        self.assertTrue(result['found'])

    def test_schema_maps_accents_and_known_aliases(self):
        columns = ['prontuario', 'Nome do Paciente', 'Data Nascimento', 'Nome da Mãe', 'NºCartSus', 'Endereço', 'Município', 'Telefone', 'Sexo']
        values = ('1', 'José', None, 'Mãe', 'CNS', 'Rua', 'Cidade', '999', 'M')
        connection = FakeConnection(columns, values)
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            data = AccessPatientService().search(self.config, '1')['data']
        self.assertEqual('José', data['nome'])
        self.assertEqual('Mãe', data['nome_mae'])
        self.assertEqual('CNS', data['cns'])
        self.assertEqual('Cidade', data['cidade'])

    def test_missing_table_has_specific_error(self):
        error = RuntimeError('42S02', 'Could not find table cadastro_de_pacientes')
        connection = FakeConnection([], None, schema_error=error)
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            with self.assertRaises(AccessLookupError) as raised:
                AccessPatientService().search(self.config, '1')
        self.assertEqual('ACCESS_TABLE_NOT_FOUND', raised.exception.code)
        self.assertTrue(connection.schema_cursor.closed)

    def test_empty_description_has_specific_error(self):
        connection = FakeConnection([], None)
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            with self.assertRaises(AccessLookupError) as raised:
                AccessPatientService().test_connection(self.config)
        self.assertEqual('ACCESS_SCHEMA_EMPTY', raised.exception.code)

    def test_missing_prontuario_column_has_specific_error(self):
        connection = FakeConnection(['Nome do Paciente'], None)
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            with self.assertRaises(AccessLookupError) as raised:
                AccessPatientService().test_connection(self.config)
        self.assertEqual('ACCESS_PRONTUARIO_COLUMN_MISSING', raised.exception.code)

    def test_negative_cache_expires_after_sixty_seconds(self):
        now = [0.0]
        connection = FakeConnection(['prontuario'], None)
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connection)
        service = AccessPatientService(clock=lambda: now[0])
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            self.assertEqual('access', service.search(self.config, '404')['source'])
            self.assertEqual('memory_cache', service.search(self.config, '404')['source'])
            now[0] = 61.0
            self.assertEqual('access', service.search(self.config, '404')['source'])

    def test_disabled_configuration_does_not_connect(self):
        service = AccessPatientService()
        with self.assertRaises(AccessLookupError) as raised:
            service.search(AccessConfig('server', 'share', 'file.accdb', False), '1')
        self.assertEqual('ACCESS_DISABLED', raised.exception.code)

    def test_cache_is_lru_bounded_and_configuration_change_invalidates_it(self):
        first_connection = FakeConnection(['prontuario'], None)
        connections = [first_connection, FakeConnection(['prontuario'], None)]
        fake_pyodbc = SimpleNamespace(drivers=lambda: [ACCESS_DRIVER], connect=lambda *a, **k: connections.pop(0))
        service = AccessPatientService(max_cache=2)
        with patch('src.services.access_patient_service.pyodbc', fake_pyodbc):
            service.search(self.config, '1')
            service.search(self.config, '2')
            service.search(self.config, '3')
            self.assertEqual(['2', '3'], list(service._cache))
            service.search(AccessConfig('other-server', 'share', 'patients.accdb'), '4')
            self.assertEqual(['4'], list(service._cache))
            self.assertTrue(first_connection.closed)


if __name__ == '__main__':
    unittest.main()
