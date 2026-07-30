import tempfile
import unittest
from datetime import date, datetime, time
from pathlib import Path

import pymupdf

from src.app import create_app
from src.extensions import db
from src.models.patient import Patient
from src.models.specialty import Specialty
from src.models.surgery_request import SurgeryRequest
from src.models.sync import DocumentTemplateArchive, GeneratedDocumentSnapshot
from src.models.user import User
from src.pdf.snapshots import create_request_snapshots, render_snapshot


class PdfSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)

        class TestConfig:
            TESTING = True
            SECRET_KEY = 'pdf-snapshot-test-key'
            BASE_DIR = root
            INSTANCE_PATH = root / 'instance'
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{root / "snapshot.db"}'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = False
            RATELIMIT_ENABLED = False
            PROTECTED_PDF_DIR = root / 'protected_pdfs'
            ADMIN_BOOTSTRAP_USERNAME = ''
            ADMIN_BOOTSTRAP_PASSWORD = ''
            SECURITY_HEADERS_ENABLED = False
            DESKTOP_MODE = False
            SYNC_ENABLED = False

        self.root = root
        self.app = create_app(TestConfig)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def test_snapshot_regenerates_baked_pdf_without_persisting_bytes(self):
        with self.app.app_context():
            specialty = Specialty(
                slug='ortopedia', name='Ortopedia', is_active=True
            )
            db.session.add(specialty)
            db.session.flush()
            user = User(
                username='medico',
                password='012345',
                full_name='Dr. Médico',
                role='solicitante',
                specialty_id=specialty.id,
                cns='123456789012345',
                crm='CRM 1234',
            )
            patient = Patient(
                nome='João da Conceição',
                prontuario='10001',
                data_nascimento=datetime(1984, 2, 29),
                sexo='M',
                nome_mae='Maria da Conceição',
                cns='987654321098765',
                cidade='Fortaleza',
                endereco='Rua de Teste, 10',
                estado='CE',
                contato='85999990000',
                diagnostico='Fratura de fêmur',
                cid='S720',
                specialty_id=specialty.id,
            )
            db.session.add_all([user, patient])
            db.session.flush()
            surgery = SurgeryRequest(
                patient_id=patient.id,
                peso=72,
                sinais_sintomas='Dor e limitação funcional',
                condicoes_justificativa='Indicação cirúrgica',
                resultados_diagnosticos='Radiografia compatível',
                procedimento_solicitado='OSTEOTOMIA',
                codigo_procedimento='0408040158',
                tipo_cirurgia='Eletiva',
                data_cirurgia=date(2026, 8, 10),
                internar_antes=True,
                hora_cirurgia=time(8, 30),
                assistente='Dra. Assistente',
                aparelhos_especiais='Arco cirúrgico',
                reserva_sangue=True,
                quantidade_sangue='2 concentrados',
                raio_x=True,
                reserva_uti=False,
                duracao_prevista='02:00',
                evolucao_internacao='Evolução estável',
                prescricao_internacao='Jejum',
                exames_preop='Hemograma',
                opme='Placa',
                specialty_id=specialty.id,
                created_by_user_id=user.id,
            )
            db.session.add(surgery)
            db.session.flush()

            snapshots = create_request_snapshots(
                patient, surgery, user
            )
            db.session.commit()
            self.assertEqual(2, len(snapshots))
            self.assertEqual(2, GeneratedDocumentSnapshot.query.count())
            self.assertEqual(2, DocumentTemplateArchive.query.count())
            self.assertFalse(list(
                self.root.rglob('Internacao_*.pdf')
            ))
            self.assertFalse(list(
                self.root.rglob('Hemocomponente_*.pdf')
            ))

            for snapshot in snapshots:
                pdf_bytes = render_snapshot(snapshot)
                document = pymupdf.open(stream=pdf_bytes, filetype='pdf')
                try:
                    expected_pages = (
                        7 if snapshot.document_type == 'internacao' else 2
                    )
                    self.assertEqual(expected_pages, document.page_count)
                    self.assertFalse(any(
                        list(page.widgets() or []) for page in document
                    ))
                finally:
                    document.close()


if __name__ == '__main__':
    unittest.main()
