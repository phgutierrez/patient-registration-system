import json
import tempfile
import unittest
from pathlib import Path

from server import create_initial_data
from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty, SpecialtyProcedure
from src.models.user import User
from src.sync import sync_service
from src.sync.crypto import decrypt_json
from tests.test_sync_real_pairing import _config


class PartialPairingRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.shared = self.root / 'shared'
        self.apps = []

    def tearDown(self):
        sync_service.stop()
        for app in self.apps:
            with app.app_context():
                db.session.remove()
        self.tempdir.cleanup()

    def _app(self, name: str):
        app = create_app(_config(self.root / name, self.shared))
        self.apps.append(app)
        with app.app_context():
            db.create_all()
        return app

    def test_retry_recovers_station_with_partially_applied_checkpoint(self):
        first = self._app('station-a')
        create_initial_data(first)
        with first.app_context():
            specialty = Specialty.query.filter_by(slug='ortopedia').one()
            db.session.add(User(
                username='medico',
                password='123456',
                full_name='Médico Teste',
                role='admin',
                specialty_id=specialty.id,
            ))
            db.session.commit()
            recovery_key = sync_service.runtime.recovery_key_once
            sync_service.enqueue_baseline()
            sync_service.sync_once()

        second = self._app('station-b')
        sync_service.pair(recovery_key)
        checkpoint = sorted(
            (self.shared / 'checkpoints').glob('*.checkpoint'), reverse=True
        )[0]
        outer = json.loads(checkpoint.read_text(encoding='utf-8'))
        payload = decrypt_json(
            sync_service.runtime.master_key,
            outer['encrypted'],
            outer['header'],
        )
        with second.app_context():
            sync_service._apply_payload(
                payload['entities'][0], 'checkpoint', 1
            )
            db.session.commit()
        sync_service.runtime.error = 'Falha antiga após restauração parcial.'

        response = second.test_client().post(
            '/sincronizacao/configurar',
            data={'action': 'retry_sync'},
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(
            302,
            response.status_code,
            msg=sync_service.runtime.error,
        )
        with second.app_context():
            self.assertEqual(1, Specialty.query.count())
            self.assertGreater(SpecialtyProcedure.query.count(), 10)
            self.assertEqual('Médico Teste', User.query.one().full_name)


if __name__ == '__main__':
    unittest.main()
