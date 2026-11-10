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

    def test_vendored_crypto_wheel_matches_declared_hash(self):
        wheel = build_exe_32bits.CRYPTO_WHEEL
        self.assertTrue(wheel.is_file())
        self.assertEqual(
            build_exe_32bits.CRYPTO_WHEEL_SHA256,
            hashlib.sha256(wheel.read_bytes()).hexdigest(),
        )
        checksum = wheel.with_suffix(wheel.suffix + '.sha256').read_text(
            encoding='utf-8'
        )
        self.assertIn(build_exe_32bits.CRYPTO_WHEEL_SHA256, checksum.lower())

    def test_batch_requires_python_311_win32_and_binary_packages(self):
        source = (ROOT / 'build_exe_32bits.bat').read_text(encoding='utf-8')
        self.assertIn('py -3.11-32', source)
        self.assertNotIn('py -3.10-32', source)
        self.assertNotIn('py -3.12-32', source)
        self.assertIn('--only-binary=:all:', source)
        self.assertIn('--no-deps --force-reinstall "%GREENLET_WHEEL%"', source)
        self.assertIn('--no-deps --force-reinstall "%CRYPTO_WHEEL%"', source)
        self.assertNotIn('--upgrade pip setuptools wheel', source)
        self.assertIn('GREENLET_SHA256=', source)

    def test_build_excludes_greenlet_test_modules(self):
        self.assertIn('greenlet.tests', build_exe_32bits.EXCLUDES)
        self.assertIn('greenlet._greenlet', build_exe_32bits.HIDDEN_IMPORTS)

    def test_frontend_bundles_are_packaged_and_complete(self):
        destinations = {destination for _, destination in build_exe_32bits.DATA_FILES}
        self.assertIn('src/static/dist', destinations)
        self.assertIn('src/static/icons', destinations)
        self.assertFalse(any('fontawesome' in str(source) for source, _ in build_exe_32bits.DATA_FILES))
        sources = {source for source, _ in build_exe_32bits.DATA_FILES}
        self.assertIn(ROOT / 'src' / 'static' / 'icon-map.json', sources)
        files = build_exe_32bits.frontend_bundle_files()
        names = {path.as_posix() for path in files}
        self.assertIn('dist/.vite/manifest.json', names)
        self.assertTrue(any(name.startswith('icons/icons-') and name.endswith('.svg') for name in names))
        self.assertTrue(any(name.startswith('dist/js/shell-') for name in names))
        # Caminhos relativos: funcionam em /static/dist e dentro do _internal do PyInstaller.
        self.assertFalse(any(name.startswith('/') or ':' in name for name in names))

    def test_missing_bundles_fail_with_clear_instruction(self):
        import tempfile
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaisesRegex(FileNotFoundError, 'npm run build'):
                build_exe_32bits.frontend_bundle_files(Path(empty), Path(empty))


if __name__ == '__main__':
    unittest.main()
