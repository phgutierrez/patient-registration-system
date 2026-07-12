import unittest

from src.services.forms_service import validate_schedule_payload


class SchedulePayloadTests(unittest.TestCase):
    def setUp(self):
        self.defaults = {
            'procedure_title': 'Procedimento original', 'date': '2026-08-20',
            'orthopedist': 'Dr. Pedro Henrique', 'full_description': 'Descrição original',
            'needs_icu': 'Não', 'opme': [], 'opme_other': '',
        }

    def test_accepts_semantic_edits_without_mutating_defaults(self):
        result = validate_schedule_payload({
            'procedure_title': 'Procedimento ajustado', 'date': '2026-09-01',
            'orthopedist': 'Dr. Sávio Bruno', 'full_description': 'Texto ajustado',
            'needs_icu': 'Sim', 'opme': ['Placa em 8'], 'opme_other': '',
        }, self.defaults)
        self.assertEqual('Procedimento ajustado', result['procedure_title'])
        self.assertEqual('Procedimento original', self.defaults['procedure_title'])

    def test_rejects_invalid_date_and_opme(self):
        with self.assertRaises(ValueError):
            validate_schedule_payload({'date': '01/09/2026'}, self.defaults)
        with self.assertRaises(ValueError):
            validate_schedule_payload({'opme': ['Opção arbitrária']}, self.defaults)
        with self.assertRaises(ValueError):
            validate_schedule_payload({'opme': ['Não se aplica', 'Placa em 8']}, self.defaults)
