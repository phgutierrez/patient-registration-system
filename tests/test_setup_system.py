import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from scripts import setup_system


class SetupSafetyTests(unittest.TestCase):
    def test_integrity_and_backup_preserve_existing_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / 'instance' / 'prontuario.db'
            database.parent.mkdir()
            with closing(sqlite3.connect(database)) as connection:
                connection.execute('CREATE TABLE sentinel (value TEXT)')
                connection.execute("INSERT INTO sentinel VALUES ('preservar')")
                connection.commit()

            with patch.object(setup_system, 'ROOT', root):
                setup_system.check_database(database)
                backup = setup_system.backup_database(database)

            self.assertTrue(backup.is_file())
            with closing(sqlite3.connect(backup)) as connection:
                self.assertEqual('preservar', connection.execute('SELECT value FROM sentinel').fetchone()[0])

    def test_corrupt_database_is_rejected_before_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'broken.db'
            database.write_bytes(b'not-a-sqlite-database')
            with self.assertRaises(sqlite3.DatabaseError):
                setup_system.check_database(database)


if __name__ == '__main__':
    unittest.main()
