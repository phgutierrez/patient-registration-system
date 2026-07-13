import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.services.windows_file_picker import (
    FilePickerError, pick_local_access_database, validate_local_access_path,
)


class WindowsFilePickerTests(unittest.TestCase):
    def test_validates_local_access_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / 'patients.accdb'
            database.touch()
            self.assertEqual(str(database), validate_local_access_path(str(database)))
        for invalid in ('patients.accdb', r'\\server\share\patients.accdb', r'C:\data\patients.txt'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_local_access_path(invalid)

    def test_picker_returns_selected_file_and_handles_cancel(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / 'patients.accdb'
            database.touch()
            selected = SimpleNamespace(returncode=0, stdout=str(database) + '\n', stderr='')
            cancelled = SimpleNamespace(returncode=0, stdout='', stderr='')
            with patch('src.services.windows_file_picker.os.name', 'nt'), \
                    patch('src.services.windows_file_picker.shutil.which', return_value='powershell.exe'), \
                    patch('src.services.windows_file_picker.subprocess.run', side_effect=[selected, cancelled]):
                self.assertEqual(str(database), pick_local_access_database())
                self.assertIsNone(pick_local_access_database())

    def test_picker_is_unavailable_outside_windows(self):
        with patch('src.services.windows_file_picker.os.name', 'posix'):
            with self.assertRaises(FilePickerError):
                pick_local_access_database()


class AccessSettingsTemplateTests(unittest.TestCase):
    def test_template_has_mutually_exclusive_sources_and_picker(self):
        source = (Path(__file__).resolve().parents[1] / 'src' / 'templates' / 'specialty_settings' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('name="access_source" value="network"', source)
        self.assertIn('name="access_source" value="local"', source)
        self.assertIn('data-access-source-section="network"', source)
        self.assertIn('data-access-source-section="local"', source)
        self.assertIn('select-local-access-btn', source)
        self.assertIn('control.disabled = !active', source)


if __name__ == '__main__':
    unittest.main()
