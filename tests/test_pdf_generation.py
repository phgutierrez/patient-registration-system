import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pymupdf
from flask import Flask

from src.pdf.generator import generate_pdf
from src.pdf.inventory import DOCUMENTS
from src.pdf.mappings import build_hemocomponente_mapping, build_internacao_mapping
from src.pdf.renderer import (
    PdfGenerationError,
    convert_legacy_coordinates,
    insert_text_fitting_box,
    mapping_to_rect,
    resolve_mapping,
)
from src.pdf.storage import atomic_write_pdf


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / 'src'


def fake_records(*, opme='', reserva_sangue=True, nome='João da Conceição Silva'):
    patient = SimpleNamespace(
        id=10, nome=nome, prontuario='123456', nome_mae='Maria da Conceição',
        contato='(83) 99999-0000', cns='123456789012345',
        data_nascimento=date(1984, 2, 29), sexo='M', cidade='João Pessoa',
        endereco='Rua de Teste, 100', diagnostico='Fratura com acentuação',
        cid='S72.0', idade=42,
    )
    surgery = SimpleNamespace(
        id=20, data_cirurgia=date(2026, 7, 20), hora_cirurgia=time(8, 30),
        internar_antes=True, opme=opme, aparelhos_especiais='Arco cirúrgico',
        sinais_sintomas='Dor persistente\nLimitação funcional',
        condicoes_justificativa='Tratamento cirúrgico indicado',
        resultados_diagnosticos='Radiografia compatível', cid_secundario='',
        procedimento_solicitado='OSTEOTOMIA', codigo_procedimento='0408040158',
        assistente='Dra. Ana', reserva_sangue=reserva_sangue,
        quantidade_sangue='2 concentrados', raio_x=True, duracao_prevista='02:00',
        peso=72, evolucao_internacao='Evolução estável',
        prescricao_internacao='Jejum e analgesia', exames_preop='Hemograma',
    )
    requester = SimpleNamespace(full_name='Dr. José Médico', cns='987654321098765', crm='CRM 1234')
    return patient, surgery, requester


class InventoryTests(unittest.TestCase):
    def test_templates_match_inventory(self):
        for identifier, spec in DOCUMENTS.items():
            with self.subTest(document=identifier):
                document = pymupdf.open(spec.template_path(APP_ROOT))
                try:
                    self.assertEqual(spec.expected_template_pages, document.page_count)
                    self.assertTrue(all(page.rect.width > 0 and page.rect.height > 0 for page in document))
                    self.assertTrue(all(page.rotation == 0 for page in document))
                    self.assertGreater(sum(len(list(page.widgets() or [])) for page in document), 0)
                finally:
                    document.close()

    def test_known_widget_counts(self):
        expected = {'internacao': 72, 'hemocomponente': 64}
        for identifier, count in expected.items():
            with self.subTest(document=identifier):
                document = pymupdf.open(DOCUMENTS[identifier].template_path(APP_ROOT))
                try:
                    self.assertEqual(count, sum(len(list(page.widgets() or [])) for page in document))
                finally:
                    document.close()


class MappingTests(unittest.TestCase):
    def test_existing_business_rules_and_accents(self):
        patient, surgery, requester = fake_records(opme='Não se aplica')
        values = build_internacao_mapping(patient, surgery, requester, datetime(2026, 7, 11, 9, 5))
        self.assertEqual('', values['OPME'])
        self.assertEqual('19/07/2026', values['DataInternacao'])
        self.assertEqual('Fem' if patient.sexo == 'F' else 'Masc', values['Sexo'])
        self.assertEqual('João da Conceição Silva', values['NomePaciente7'])
        self.assertEqual('83999990000', values['TelContato'])

    def test_hemocomponent_aliases_and_corrupt_field_name(self):
        patient, surgery, requester = fake_records()
        values = build_hemocomponente_mapping(patient, surgery, requester)
        match = resolve_mapping('Diagn�stico e Indica��o Cl�nica', values)
        self.assertIsNotNone(match)
        self.assertEqual('Reserva para cirurgia', match[1])
        self.assertEqual('', values['DATA'])
        self.assertEqual('X', values['PROGRAMADA Para determinada data e horaml de Concentrado de Hemácias'])

    def test_hemocomponent_weight_calculation(self):
        patient, surgery, requester = fake_records()
        for weight, expected_weight, expected_calculation in (
            (72, '72', '720'),
            (72.5, '72.5', '725'),
            (None, '', ''),
            ('inválido', '', ''),
        ):
            with self.subTest(weight=weight):
                surgery.peso = weight
                values = build_hemocomponente_mapping(patient, surgery, requester)
                self.assertEqual(expected_weight, values['Peso'])
                self.assertEqual(expected_calculation, values['Texto5'])


class RendererTests(unittest.TestCase):
    def _assert_final_pdf(self, pdf_bytes, pages):
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))
        document = pymupdf.open(stream=pdf_bytes, filetype='pdf')
        try:
            self.assertEqual(pages, document.page_count)
            self.assertEqual(0, sum(len(list(page.widgets() or [])) for page in document))
            self.assertTrue(all(page.get_contents() for page in document))
        finally:
            document.close()

    def test_internacao_five_and_seven_pages(self):
        patient, surgery, requester = fake_records(opme='')
        values = build_internacao_mapping(patient, surgery, requester)
        self._assert_final_pdf(generate_pdf('internacao', values, APP_ROOT), 5)
        surgery.opme = 'Placa bloqueada'
        values = build_internacao_mapping(patient, surgery, requester)
        self._assert_final_pdf(generate_pdf('internacao', values, APP_ROOT), 7)

    def test_hemocomponent_is_baked(self):
        patient, surgery, requester = fake_records()
        values = build_hemocomponente_mapping(
            patient, surgery, requester, datetime(2031, 12, 24, 14, 30),
        )
        pdf_bytes = generate_pdf('hemocomponente', values, APP_ROOT)
        self._assert_final_pdf(pdf_bytes, 2)
        document = pymupdf.open(stream=pdf_bytes, filetype='pdf')
        try:
            text = '\n'.join(page.get_text() for page in document)
            self.assertIn('Reserva para cirurgia', text)
            self.assertIn('720', text)
            self.assertIn('29/02/1984', text)
            self.assertNotIn('24/12/2031', text)
        finally:
            document.close()

    def test_hemocomponent_without_weight_remains_valid(self):
        patient, surgery, requester = fake_records()
        surgery.peso = None
        values = build_hemocomponente_mapping(patient, surgery, requester)
        self.assertEqual('', values['Texto5'])
        self._assert_final_pdf(generate_pdf('hemocomponente', values, APP_ROOT), 2)

    def test_only_selected_radio_option_is_marked(self):
        patient, surgery, requester = fake_records()
        patient.sexo = 'F'
        values = build_internacao_mapping(patient, surgery, requester)
        pdf_bytes = generate_pdf('internacao', values, APP_ROOT)
        document = pymupdf.open(stream=pdf_bytes, filetype='pdf')
        try:
            page = document[0]
            masc = page.get_pixmap(
                clip=pymupdf.Rect(418.0, 176.3, 426.5, 187.0),
                colorspace=pymupdf.csGRAY,
                alpha=False,
            )
            fem = page.get_pixmap(
                clip=pymupdf.Rect(469.8, 176.3, 478.3, 187.0),
                colorspace=pymupdf.csGRAY,
                alpha=False,
            )
            self.assertLess(sum(fem.samples) / len(fem.samples), sum(masc.samples) / len(masc.samples))
        finally:
            document.close()

    def test_long_multiline_and_accented_content(self):
        patient, surgery, requester = fake_records(nome='Álvaro Çedilha ' + 'Nome Muito Longo ' * 5)
        surgery.sinais_sintomas = 'Linha acentuada çãõ\n' * 15
        values = build_internacao_mapping(patient, surgery, requester)
        self._assert_final_pdf(generate_pdf('internacao', values, APP_ROOT), 5)

    def test_missing_required_field_fails(self):
        with self.assertRaises(PdfGenerationError):
            generate_pdf('internacao', {'NomePaciente1': 'Teste'}, APP_ROOT)

    def test_coordinate_helpers(self):
        rect = mapping_to_rect({'x': 10, 'y': 20, 'width': 40, 'height': 30})
        self.assertEqual(pymupdf.Rect(10, 20, 50, 50), rect)
        document = pymupdf.open()
        page = document.new_page(width=200, height=300)
        converted = convert_legacy_coordinates(
            page, {'x': 10, 'y': 20, 'width': 40, 'height': 30, 'origin': 'bottom'}
        )
        self.assertEqual(pymupdf.Rect(10, 250, 50, 280), converted)
        page.set_rotation(90)
        rotated = convert_legacy_coordinates(
            page, {'x': 10, 'y': 20, 'width': 40, 'height': 30, 'origin': 'bottom'}
        )
        self.assertFalse(rotated.is_empty)
        document.close()

    def test_text_fitting_reports_overflow(self):
        document = pymupdf.open()
        page = document.new_page()
        with self.assertRaises(PdfGenerationError):
            insert_text_fitting_box(page, pymupdf.Rect(0, 0, 5, 5), 'texto longo', 12, 10)
        document.close()


class ConcurrencyTests(unittest.TestCase):
    def test_concurrent_generation_and_atomic_storage(self):
        def generate(index):
            patient, surgery, requester = fake_records(nome=f'Paciente Concorrente {index}')
            values = build_internacao_mapping(patient, surgery, requester)
            return index, generate_pdf('internacao', values, APP_ROOT)

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(generate, range(4)))
        self.assertEqual(4, len({pdf_bytes for _, pdf_bytes in results}))

        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, pdf_bytes in results:
                path = atomic_write_pdf(Path(directory) / f'{index}.pdf', pdf_bytes)
                paths.append(path)
            self.assertTrue(all(path.is_file() and path.stat().st_size > 1024 for path in paths))
            self.assertFalse(list(Path(directory).glob('*.tmp')))


class HttpDeliveryTests(unittest.TestCase):
    def test_pdf_response_is_binary_no_store_and_has_length(self):
        from src.routes.surgery import _send_authorized_pdf

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'documento.pdf'
            path.write_bytes(b'%PDF-1.4\n%%EOF\n')
            app = Flask(__name__)
            surgery = SimpleNamespace(patient_id=10)
            with app.test_request_context('/surgery/1/pdf/view'):
                with patch('src.routes.surgery.ensure_surgery_access', return_value=None), \
                     patch('src.routes.surgery.get_protected_pdf_path', return_value=path):
                    response = _send_authorized_pdf(
                        surgery, path.name, 'Internacao_10.pdf', as_attachment=False
                    )
            self.assertEqual('application/pdf', response.mimetype)
            self.assertEqual('no-store', response.headers['Cache-Control'])
            self.assertEqual(str(path.stat().st_size), response.headers['Content-Length'])
            self.assertIn('inline', response.headers['Content-Disposition'])
            self.assertEqual('SAMEORIGIN', response.headers['X-Frame-Options'])
            self.assertIn("frame-ancestors 'self'", response.headers['Content-Security-Policy'])
            self.assertIn("frame-ancestors 'self'", response.headers['Content-Security-Policy-Report-Only'])
            response.close()

    def test_download_does_not_receive_inline_frame_permission(self):
        from src.routes.surgery import _send_authorized_pdf

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'documento.pdf'
            path.write_bytes(b'%PDF-1.4\n%%EOF\n')
            app = Flask(__name__)
            surgery = SimpleNamespace(patient_id=10)
            with app.test_request_context('/surgery/1/pdf'):
                with patch('src.routes.surgery.ensure_surgery_access', return_value=None), \
                     patch('src.routes.surgery.get_protected_pdf_path', return_value=path):
                    response = _send_authorized_pdf(
                        surgery, path.name, 'Internacao_10.pdf', as_attachment=True
                    )
            self.assertIn('attachment', response.headers['Content-Disposition'])
            self.assertNotEqual('SAMEORIGIN', response.headers.get('X-Frame-Options'))
            self.assertNotIn("frame-ancestors 'self'", response.headers.get('Content-Security-Policy', ''))
            response.close()


if __name__ == '__main__':
    unittest.main()
