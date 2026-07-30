import json
import tempfile
import unittest
from pathlib import Path

from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty
from src.models.user import User
from src.sync import sync_service
from src.sync.clock import HybridLogicalClock
from src.sync.crypto import (
    SyncCryptoError,
    decrypt_json,
    encrypt_json,
    format_recovery_key,
    generate_master_key,
)


def station_config(root: Path, shared: Path):
    database = root / 'instance' / 'station.db'
    database.parent.mkdir(parents=True, exist_ok=True)
    return type('StationConfig', (), {
        'TESTING': True,
        'SECRET_KEY': f'test-secret-{root.name}',
        'BASE_DIR': root,
        'INSTANCE_PATH': database.parent,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': False,
        'PROTECTED_PDF_DIR': root / 'pdfs',
        'ADMIN_BOOTSTRAP_USERNAME': '',
        'ADMIN_BOOTSTRAP_PASSWORD': '',
        'SECURITY_HEADERS_ENABLED': False,
        'DESKTOP_MODE': False,
        'SYNC_ENABLED': True,
        'SYNC_ROOT': str(shared),
        'SYNC_START_WORKER': False,
        'SYNC_INTERVAL_SECONDS': 5,
    })


class CryptoAndClockTests(unittest.TestCase):
    def test_aes_gcm_rejects_tampering_and_wrong_key(self):
        key = generate_master_key()
        header = {'deployment_id': 'test', 'sequence': 1}
        encrypted = encrypt_json(key, {'nome': 'Paciente Teste'}, header)
        self.assertEqual(
            {'nome': 'Paciente Teste'},
            decrypt_json(key, encrypted, header),
        )

        tampered = dict(encrypted)
        tampered['ciphertext'] = (
            ('A' if encrypted['ciphertext'][0] != 'A' else 'B')
            + encrypted['ciphertext'][1:]
        )
        with self.assertRaises(SyncCryptoError):
            decrypt_json(key, tampered, header)
        with self.assertRaises(SyncCryptoError):
            decrypt_json(generate_master_key(), encrypted, header)

    def test_hybrid_clock_advances_after_remote_counter(self):
        clock = HybridLogicalClock('device-b')
        clock.observe('9999999999999:00000042:device-a:event')
        order, _ = clock.next()
        self.assertGreater(order, '9999999999999:00000042:device-a:event')
        self.assertIn(':00000043:', order)


class TwoStationSyncTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.shared = self.root / 'shared'
        self.station_a = self.root / 'station-a'
        self.station_b = self.root / 'station-b'
        self.apps = []

    def tearDown(self):
        sync_service.stop()
        for app in self.apps:
            with app.app_context():
                db.session.remove()
        self.tempdir.cleanup()

    def _app(self, root):
        app = create_app(station_config(root, self.shared))
        self.apps.append(app)
        with app.app_context():
            db.create_all()
        return app

    def test_pair_checkpoint_events_and_field_level_merge(self):
        app_a = self._app(self.station_a)
        with app_a.app_context():
            specialty = Specialty(
                slug='ortopedia', name='Ortopedia', is_active=True
            )
            db.session.add(specialty)
            db.session.flush()
            user = User(
                username='medico',
                password='012345',
                full_name='Médico Inicial',
                role='solicitante',
                specialty_id=specialty.id,
            )
            db.session.add(user)
            db.session.commit()
            recovery = sync_service.runtime.recovery_key_once
            self.assertTrue(recovery)
            sync_service.sync_once()
            self.assertTrue(list(
                (self.shared / 'events').rglob('*.event')
            ))
            self.assertTrue(list(
                (self.shared / 'checkpoints').glob('*.checkpoint')
            ))
            raw_event = next((self.shared / 'events').rglob('*.event')).read_text(
                encoding='utf-8'
            )
            self.assertNotIn('Médico Inicial', raw_event)
            self.assertNotIn('012345', raw_event)

        app_b = self._app(self.station_b)
        self.assertTrue(sync_service.runtime.pairing_required)
        with self.assertRaises(SyncCryptoError):
            sync_service.pair(format_recovery_key(generate_master_key()))
        sync_service.pair(recovery)
        with app_b.app_context():
            restored = sync_service.restore_latest_checkpoint()
            self.assertGreaterEqual(restored, 2)
            sync_service.sync_once()
            user_b = User.query.filter_by(username='medico').one()
            self.assertEqual('Médico Inicial', user_b.full_name)

        # A altera o nome sem tocar no CRM.
        sync_service.configure(app_a)
        with app_a.app_context():
            user_a = User.query.filter_by(username='medico').one()
            user_a.full_name = 'Médico Atualizado em A'
            db.session.commit()
            sync_service.sync_once()

        # B altera outro campo antes de consumir a mudança de A.
        sync_service.configure(app_b)
        with app_b.app_context():
            user_b = User.query.filter_by(username='medico').one()
            user_b.crm = 'CRM 12345'
            db.session.commit()
            sync_service.sync_once()
            self.assertEqual('Médico Atualizado em A', user_b.full_name)
            self.assertEqual('CRM 12345', user_b.crm)

        sync_service.configure(app_a)
        with app_a.app_context():
            sync_service.sync_once()
            user_a = User.query.filter_by(username='medico').one()
            self.assertEqual('Médico Atualizado em A', user_a.full_name)
            self.assertEqual('CRM 12345', user_a.crm)

        manifest = json.loads(
            (self.shared / 'deployment.json').read_text(encoding='utf-8')
        )
        self.assertEqual(1, manifest['sync_schema_version'])
        self.assertNotEqual(
            sync_service.runtime.device_uuid,
            'sync-disabled',
        )


if __name__ == '__main__':
    unittest.main()
