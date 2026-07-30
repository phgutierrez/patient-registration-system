import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from types import SimpleNamespace

from src.services.external_coordination import acquire_forms_lock
from src.services.local_runtime import (
    _copy_distribution,
    _deployment_manifest,
    _migrate_legacy_database,
    is_remote_path,
)
from src.sync import sync_service


class LocalRuntimeTests(unittest.TestCase):
    def test_unc_is_remote_and_distribution_excludes_mutable_data(self):
        self.assertTrue(is_remote_path(Path(r'\\servidor\pasta\Sistema')))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            destination = root / 'local-copy'
            (source / '_internal').mkdir(parents=True)
            (source / '_internal' / 'asset.txt').write_text(
                'asset', encoding='utf-8'
            )
            (source / 'PatientRegistration.exe').write_bytes(b'exe')
            (source / 'instance').mkdir()
            (source / 'instance' / 'prontuario.db').write_bytes(b'private')
            (source / '.env').write_text('SECRET_KEY=private', encoding='utf-8')

            _copy_distribution(source, destination)
            self.assertTrue(
                (destination / '_internal' / 'asset.txt').is_file()
            )
            self.assertTrue(
                (destination / 'PatientRegistration.exe').is_file()
            )
            self.assertFalse((destination / 'instance').exists())
            self.assertFalse((destination / '.env').exists())

    def test_only_first_station_receives_consistent_legacy_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'distribution'
            shared = source / '_shared_data'
            source_db = source / 'instance' / 'prontuario.db'
            source_db.parent.mkdir(parents=True)
            with closing(sqlite3.connect(source_db)) as connection:
                connection.execute(
                    'CREATE TABLE patient (id INTEGER PRIMARY KEY, nome TEXT)'
                )
                connection.execute(
                    'INSERT INTO patient(nome) VALUES (?)', ('Paciente Legado',)
                )
                connection.commit()
            manifest = _deployment_manifest(shared)
            self.assertTrue(manifest['deployment_id'])

            first = root / 'local-first'
            second = root / 'local-second'
            _migrate_legacy_database(source, first, shared)
            _migrate_legacy_database(source, second, shared)

            first_db = first / 'instance' / 'prontuario.db'
            self.assertTrue(first_db.is_file())
            with closing(sqlite3.connect(first_db)) as connection:
                self.assertEqual(
                    'Paciente Legado',
                    connection.execute(
                        'SELECT nome FROM patient'
                    ).fetchone()[0],
                )
                self.assertEqual(
                    'ok', connection.execute('PRAGMA quick_check').fetchone()[0]
                )
            self.assertFalse((second / 'instance' / 'prontuario.db').exists())
            self.assertTrue(list(
                (first / 'migration_backup').rglob('prontuario.db')
            ))


class ExternalCoordinationTests(unittest.TestCase):
    def setUp(self):
        self.previous_runtime = sync_service.runtime

    def tearDown(self):
        sync_service.runtime = self.previous_runtime

    def test_forms_lock_is_exclusive_and_uses_only_uuids(self):
        with tempfile.TemporaryDirectory() as directory:
            shared = Path(directory)
            sync_service.runtime = SimpleNamespace(
                ready=True,
                shared_root=shared,
                device_uuid='11111111-1111-1111-1111-111111111111',
            )
            entity_uuid = '22222222-2222-2222-2222-222222222222'
            first = acquire_forms_lock(entity_uuid)
            second = acquire_forms_lock(entity_uuid)
            self.assertTrue(first.acquired)
            self.assertTrue(second.available)
            self.assertFalse(second.acquired)
            self.assertEqual(entity_uuid, first.path.name)
            owner = json.loads(
                (first.path / 'owner.json').read_text(encoding='utf-8')
            )
            self.assertEqual(first.attempt_uuid, owner['attempt_uuid'])
            first.release()
            third = acquire_forms_lock(entity_uuid)
            self.assertTrue(third.acquired)
            third.release()

    def test_vendored_crypto_wheel_hash(self):
        wheel = (
            Path(__file__).resolve().parents[1]
            / 'build_support'
            / 'pycryptodome-3.23.0-cp37-abi3-win32.whl'
        )
        self.assertTrue(wheel.is_file())
        self.assertEqual(
            '507dbead45474b62b2bbe318eb1c4c8ee641077532067fec9c1aa82c31f84886',
            hashlib.sha256(wheel.read_bytes()).hexdigest(),
        )


if __name__ == '__main__':
    unittest.main()
