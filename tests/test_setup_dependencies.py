import hashlib
import unittest
from pathlib import Path

from scripts import install_windows_dependencies as installer


ROOT = Path(__file__).resolve().parents[1]


class SetupDependenciesTests(unittest.TestCase):
    def test_vendored_wheel_is_present_and_valid(self):
        self.assertTrue(installer.GREENLET_WHEEL.is_file())
        self.assertEqual(
            installer.GREENLET_SHA256,
            hashlib.sha256(installer.GREENLET_WHEEL.read_bytes()).hexdigest(),
        )

    def test_pip_error_classification(self):
        self.assertEqual(
            'BINARY_UNAVAILABLE',
            installer.classify_pip_failure('No matching distribution found for package'),
        )
        self.assertEqual(
            'NETWORK_ERROR',
            installer.classify_pip_failure('Failed to establish a new connection'),
        )
        self.assertEqual('PIP_ERROR', installer.classify_pip_failure('unknown pip failure'))

    def test_setup_forbids_source_builds_and_uses_local_greenlet(self):
        batch = (ROOT / 'setup_windows.bat').read_text(encoding='utf-8')
        installer_source = (ROOT / 'scripts' / 'install_windows_dependencies.py').read_text(encoding='utf-8')
        self.assertIn('install_windows_dependencies.py', batch)
        self.assertIn('greenlet-2.0.2-cp311-cp311-win32.whl', batch)
        self.assertIn("'--only-binary=:all:'", installer_source)
        self.assertIn("'--no-deps', '--force-reinstall'", installer_source)
        self.assertNotIn('pip install -r requirements.txt', batch)
        self.assertNotIn('--no-binary', installer_source)


if __name__ == '__main__':
    unittest.main()
