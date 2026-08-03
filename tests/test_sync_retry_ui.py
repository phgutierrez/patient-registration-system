import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.app import create_app
from src.extensions import db
from src.sync import sync_service


def _config(root: Path, shared: Path):
    database = root / 'instance' / 'station.db'
    database.parent.mkdir(parents=True, exist_ok=True)
    return type('SyncRetryConfig', (), {
        'TESTING': True,
        'SECRET_KEY': 'sync-retry-test',
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


class SyncRetryUiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.app = create_app(_config(root / 'station', root / 'shared'))
        with self.app.app_context():
            db.create_all()
        self.runtime = sync_service.runtime
        self.runtime.recovery_key_once = None
        self.runtime.pairing_required = False
        self.runtime.master_key = b'k' * 32
        self.runtime.error = 'Compartilhamento temporariamente indisponível.'
        self.client = self.app.test_client()

    def tearDown(self):
        sync_service.stop()
        with self.app.app_context():
            db.session.remove()
        self.tempdir.cleanup()

    def test_failed_pairing_always_shows_recovery_actions(self):
        response = self.client.get(
            '/sincronizacao/configurar',
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn('Tentar sincronizar novamente', body)
        self.assertIn('Recarregar acesso à pasta', body)
        self.assertIn('Informar a chave de recuperação novamente', body)

    def test_retry_clears_error_and_finishes_pairing(self):
        with (
            patch.object(sync_service, 'restore_latest_checkpoint', return_value=0),
            patch.object(sync_service, 'sync_once', return_value={'ready': True}),
            patch.object(sync_service, 'enqueue_baseline', return_value=0),
            patch.object(sync_service, 'start'),
            patch.object(sync_service, 'wake'),
        ):
            response = self.client.post(
                '/sincronizacao/configurar',
                data={'action': 'retry_sync'},
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
        self.assertEqual(302, response.status_code)
        self.assertIsNone(self.runtime.error)
        self.assertTrue(
            (self.runtime.local_root / 'recovery.confirmed').is_file()
        )

    def test_retry_failure_keeps_retry_button_visible(self):
        with patch.object(
            sync_service,
            'restore_latest_checkpoint',
            side_effect=OSError('pasta offline'),
        ):
            response = self.client.post(
                '/sincronizacao/configurar',
                data={'action': 'retry_sync'},
                environ_base={'REMOTE_ADDR': '127.0.0.1'},
            )
        self.assertEqual(200, response.status_code)
        self.assertIn('pasta offline', self.runtime.error)
        self.assertIn(
            'Tentar sincronizar novamente', response.get_data(as_text=True)
        )


if __name__ == '__main__':
    unittest.main()
