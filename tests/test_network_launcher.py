import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NetworkLauncherTests(unittest.TestCase):
    def test_launcher_files_and_build_integration_are_present(self):
        batch = (ROOT / 'Iniciar_Sistema_Rede.bat').read_text(encoding='utf-8')
        script = (ROOT / 'launcher_network.ps1').read_text(encoding='utf-8')
        build = (ROOT / 'build_exe_32bits.py').read_text(encoding='utf-8')

        self.assertIn('launcher_network.ps1', batch)
        self.assertIn('PRS_LOCAL_DATA_ROOT', script)
        self.assertIn('$env:SYNC_ROOT', script)
        self.assertIn('Test-LocalDistribution', script)
        self.assertIn('NETWORK_LAUNCHER_FILES', build)

    @unittest.skipUnless(
        os.name == 'nt' and shutil.which('powershell.exe'),
        'requer Windows PowerShell',
    )
    def test_prepare_only_copies_and_reuses_valid_local_distribution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            internal = source / '_internal'
            internal.mkdir(parents=True)
            executable = source / 'PatientRegistration.exe'
            executable.write_bytes(b'fake-executable-for-launcher-test')
            (internal / 'python311.dll').write_bytes(b'fake-python-dll')
            executable_hash = hashlib.sha256(executable.read_bytes()).hexdigest()
            (source / 'build_manifest.json').write_text(
                json.dumps({
                    'application': 'PatientRegistration',
                    'version': 'test-1',
                    'executable_sha256': executable_hash,
                }),
                encoding='utf-8',
            )
            (source / '.env').write_text('MUST_NOT_COPY=1', encoding='utf-8')
            (source / 'instance').mkdir()
            (source / 'instance' / 'prontuario.db').write_bytes(b'data')

            command = [
                shutil.which('powershell.exe'), '-NoLogo', '-NoProfile',
                '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
                str(ROOT / 'launcher_network.ps1'),
                '-SourceRoot', str(source),
                '-LocalProductRoot', str(root / 'local'),
                '-SharedDataRoot', str(root / 'shared'),
                '-PrepareOnly',
            ]
            first = subprocess.run(
                command, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            second = subprocess.run(
                command, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn('[OK] A vers', second.stdout)

            local_executables = list(
                (root / 'local' / 'applications').rglob('PatientRegistration.exe')
            )
            self.assertEqual(len(local_executables), 1)
            local_app = local_executables[0].parent
            self.assertTrue((local_app / '_internal' / 'python311.dll').is_file())
            self.assertFalse((local_app / '.env').exists())
            self.assertFalse((local_app / 'instance').exists())
            self.assertTrue((root / 'shared' / 'deployment.json').is_file())
            self.assertTrue(any((root / 'local' / 'data').iterdir()))


if __name__ == '__main__':
    unittest.main()
