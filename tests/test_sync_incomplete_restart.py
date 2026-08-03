import tempfile
import unittest
from pathlib import Path

from src.sync.runtime import initialize_runtime


class IncompletePairingRestartTests(unittest.TestCase):
    def test_secondary_station_reopens_in_retry_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shared = root / 'shared'
            first = initialize_runtime({
                'SYNC_ENABLED': True,
                'BASE_DIR': root / 'station-a',
                'SYNC_ROOT': str(shared),
            })
            self.assertTrue(first.recovery_key_once)

            second_config = {
                'SYNC_ENABLED': True,
                'BASE_DIR': root / 'station-b',
                'SYNC_ROOT': str(shared),
            }
            second = initialize_runtime(second_config)
            second.pair(first.recovery_key_once)
            self.assertFalse(second.pairing_required)
            self.assertFalse(
                (second.local_root / 'recovery.confirmed').exists()
            )

            restarted = initialize_runtime(second_config)
            self.assertIsNone(restarted.recovery_key_once)
            self.assertFalse(restarted.pairing_required)
            self.assertIsNotNone(restarted.master_key)
            self.assertIn('pareamento anterior', restarted.error.casefold())


if __name__ == '__main__':
    unittest.main()
