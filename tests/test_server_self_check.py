import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ServerSelfCheckTests(unittest.TestCase):
    def test_self_check_initializes_isolated_application(self):
        with tempfile.TemporaryDirectory(prefix='prs-self-check-') as directory:
            data_dir = Path(directory)
            environment = os.environ.copy()
            environment.update({
                'SYNC_ENABLED': 'false',
                'PATIENT_REGISTRATION_NO_DIALOG': '1',
                'PYTHONUTF8': '1',
            })
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'server.py'),
                    '--self-check',
                    '--no-browser',
                    '--data-dir',
                    str(data_dir),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=45,
            )
            self.assertEqual(
                0,
                result.returncode,
                msg=f'{result.stdout}\n{result.stderr}',
            )
            database = data_dir / 'instance' / 'prontuario.db'
            self.assertTrue(database.is_file())
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(
                    'ok',
                    connection.execute('PRAGMA quick_check').fetchone()[0],
                )
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            self.assertIn('sync_outbox', tables)
            self.assertIn('document_template_archives', tables)


if __name__ == '__main__':
    unittest.main()
