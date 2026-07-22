import unittest
from pathlib import Path


class PatientAccessFrontendTests(unittest.TestCase):
    def test_mother_name_uses_canonical_key_and_dispatches_input(self):
        template = Path('src/templates/patient/new.html').read_text(encoding='utf-8')
        script = Path('src/static/js/pages/patient-new.js').read_text(encoding='utf-8')
        self.assertIn('name="nome_mae"', template)
        self.assertIn("['nome_mae', 'nome da mãe'", script)
        self.assertIn("normalize('NFD')", script)
        self.assertIn("assignValue('nome_mae'", script)
        self.assertIn("input.dispatchEvent(new Event(eventName, { bubbles: true }))", script)


if __name__ == '__main__':
    unittest.main()
