import hashlib
import unittest
from pathlib import Path

import build_exe_32bits


ROOT = Path(__file__).resolve().parents[1]


class Build32BitsConfigurationTests(unittest.TestCase):
    def test_vendored_greenlet_wheel_matches_declared_hash(self):
        wheel = build_exe_32bits.GREENLET_WHEEL
        self.assertTrue(wheel.is_file())
        self.assertEqual(
            build_exe_32bits.GREENLET_WHEEL_SHA256,
            hashlib.sha256(wheel.read_bytes()).hexdigest(),
        )
        checksum = wheel.with_suffix(wheel.suffix + '.sha256').read_text(encoding='utf-8')
        self.assertIn(build_exe_32bits.GREENLET_WHEEL_SHA256, checksum.lower())

    def test_batch_requires_python_311_win32_and_binary_packages(self):
        source = (ROOT / 'build_exe_32bits.bat').read_text(encoding='utf-8')
        self.assertIn('py -3.11-32', source)
        self.assertNotIn('py -3.10-32', source)
        self.assertNotIn('py -3.12-32', source)
        self.assertIn('--only-binary=:all:', source)
        self.assertIn('--no-deps --force-reinstall "%GREENLET_WHEEL%"', source)
        self.assertNotIn('--upgrade pip setuptools wheel', source)
        self.assertIn('GREENLET_SHA256=', source)

    def test_build_excludes_greenlet_test_modules(self):
        self.assertIn('greenlet.tests', build_exe_32bits.EXCLUDES)
        self.assertIn('greenlet._greenlet', build_exe_32bits.HIDDEN_IMPORTS)


if __name__ == '__main__':
    unittest.main()
