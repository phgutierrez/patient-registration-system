import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.app import create_app
from src.extensions import db
from src.models.patient import Patient
from src.models.specialty import Specialty
from src.models.sync import SyncOutbox
from src.sync import sync_service


def _config(root: Path, shared: Path):
    database = root / 'instance' / 'station.db'
    database.parent.mkdir(parents=True, exist_ok=True)
    return type('TombstoneConfig', (), {
        'TESTING': True,
        'SECRET_KEY': 'sync-tombstone-test',
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


def _patient(prontuario: str, specialty_id: int) -> Patient:
    return Patient(
        nome=f'Paciente {prontuario}',
        prontuario=prontuario,
        data_nascimento=datetime(1980, 1, 1),
        sexo='M',
        nome_mae='Mãe Teste',
        cns=f'{int(prontuario):015d}',
        cidade='Fortaleza',
        endereco='',
        estado='CE',
        contato='85999999999',
        diagnostico='Diagnóstico',
        cid='M00',
        specialty_id=specialty_id,
    )


class SyncTombstoneTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.app = create_app(_config(root / 'station', root / 'shared'))
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        sync_service.stop()
        with self.app.app_context():
            db.session.remove()
        self.tempdir.cleanup()

    def test_orm_delete_becomes_versioned_tombstone(self):
        with self.app.app_context():
            specialty = Specialty(
                slug='ortopedia', name='Ortopedia', is_active=True
            )
            db.session.add(specialty)
            db.session.flush()
            patient = _patient('101', specialty.id)
            db.session.add(patient)
            db.session.commit()
            patient_uuid = patient.sync_uuid

            db.session.delete(patient)
            db.session.commit()

            archived = Patient.query.filter_by(sync_uuid=patient_uuid).one()
            self.assertTrue(archived.sync_deleted)
            self.assertIn('_deleted', archived.get_sync_field_versions())
            payloads = [
                json.loads(row.payload_json)
                for row in SyncOutbox.query.filter_by(
                    entity_uuid=patient_uuid
                ).all()
            ]
            self.assertTrue(any(
                payload['changes'].get('_deleted') is True
                for payload in payloads
            ))

    def test_duplicate_patient_archiving_versions_the_decision(self):
        with self.app.app_context():
            specialty = Specialty(
                slug='ortopedia', name='Ortopedia', is_active=True
            )
            db.session.add(specialty)
            db.session.flush()
            older = _patient('201', specialty.id)
            newer = _patient('202', specialty.id)
            db.session.add_all([older, newer])
            db.session.commit()

            older_versions = older.get_sync_field_versions()
            newer_versions = newer.get_sync_field_versions()
            older_versions['prontuario'] = (
                '0000000001000:00000001:station-a:older'
            )
            newer_versions['prontuario'] = (
                '0000000002000:00000001:station-b:newer'
            )
            older.set_sync_field_versions(older_versions)
            newer.set_sync_field_versions(newer_versions)
            newer.prontuario = older.prontuario
            db.session.flush()

            sync_service._canonicalize_patient(
                newer, '0000000002000:00000001:station-b:event'
            )
            db.session.commit()

            self.assertFalse(newer.sync_deleted)
            self.assertTrue(older.sync_deleted)
            self.assertEqual(newer.sync_uuid, older.superseded_by_uuid)
            decision_versions = older.get_sync_field_versions()
            self.assertIn('_deleted', decision_versions)
            self.assertIn('superseded_by_uuid', decision_versions)


if __name__ == '__main__':
    unittest.main()
