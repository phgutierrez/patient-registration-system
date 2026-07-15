import unittest
from pathlib import Path


class PatientAccessFrontendTests(unittest.TestCase):
    def test_mother_name_uses_canonical_key_and_dispatches_input(self):
        template = Path('src/templates/patient/new.html').read_text(encoding='utf-8')
        self.assertIn("['nome_mae', 'nome da mãe'", template)
        self.assertIn("normalize('NFD')", template)
        self.assertIn("nomeMaeInput.dispatchEvent(new Event('input', { bubbles: true }))", template)


if __name__ == '__main__':
    unittest.main()
