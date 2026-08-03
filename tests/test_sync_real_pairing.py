import tempfile
import unittest
from pathlib import Path

from server import create_initial_data
from src.app import create_app
from src.extensions import db
from src.models.specialty import Specialty, SpecialtyProcedure, SpecialtySettings
from src.models.sync import DocumentTemplateArchive
from src.models.user import User
from src.pdf.snapshots import migrate_legacy_document_snapshots
from src.sync import sync_service


def _config(root: Path, shared: Path):
    database = root / 'instance' / 'station.db'
    database.parent.mkdir(parents=True, exist_ok=True)
    return type('RealPairingConfig', (), {
        'TESTING': True,
        'SECRET_KEY': f'real-pairing-{root.name}',
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
        'ORTOPEDIA_AGENDA_URL': 'https://example.invalid/calendar.ics',
        'GOOGLE_CALENDAR_ICS_URL': 'https://example.invalid/calendar.ics',
        'GOOGLE_CALENDAR_ID': 'calendar-test',
        'GOOGLE_FORMS_VIEWFORM_URL': 'https://example.invalid/form',
    })


class RealPairingTests(unittest.TestCase):
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

    def test_second_station_pairs_through_route_with_real_baseline(self):
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
            migrate_legacy_document_snapshots()
            db.session.commit()
            recovery_key = sync_service.runtime.recovery_key_once
            sync_service.enqueue_baseline()
            sync_service.sync_once()

        second = self._app('station-b')
        self.assertTrue(sync_service.runtime.pairing_required)
        response = second.test_client().post(
            '/sincronizacao/configurar',
            data={'action': 'pair', 'recovery_key': recovery_key},
            environ_base={'REMOTE_ADDR': '127.0.0.1'},
        )
        self.assertEqual(
            302, response.status_code,
            msg=f"runtime_error={sync_service.runtime.error} body={response.get_data(as_text=True)[:1000]}",
        )
        self.assertIsNone(sync_service.runtime.error)
        with second.app_context():
            self.assertEqual(1, Specialty.query.count())
            self.assertEqual(1, SpecialtySettings.query.count())
            self.assertGreater(SpecialtyProcedure.query.count(), 10)
            self.assertEqual('Médico Teste', User.query.one().full_name)
            self.assertEqual(2, DocumentTemplateArchive.query.count())


if __name__ == '__main__':
    unittest.main()
