import unittest
from datetime import datetime, timedelta

from src.services import lifecycle


class LifecycleStateTests(unittest.TestCase):
    def setUp(self):
        lifecycle.state['sessions'].clear()
        lifecycle.state['had_sessions'] = False
        lifecycle.state['empty_since'] = None

    def test_clean_browser_close_records_empty_time(self):
        lifecycle.touch_session('local-session')
        self.assertIn('local-session', lifecycle.state['sessions'])
        lifecycle.remove_session('local-session')
        self.assertFalse(lifecycle.state['sessions'])
        self.assertIsNotNone(lifecycle.state['empty_since'])

    def test_navigation_heartbeat_cancels_pending_close(self):
        lifecycle.touch_session('local-session')
        lifecycle.remove_session('local-session')
        lifecycle.touch_session('local-session')
        self.assertIsNone(lifecycle.state['empty_since'])

    def test_shutdown_only_after_fifteen_second_grace(self):
        now = datetime.utcnow()
        lifecycle.state['had_sessions'] = True
        lifecycle.state['empty_since'] = now
        self.assertFalse(lifecycle.should_shutdown(now + timedelta(seconds=14), 15))
        self.assertTrue(lifecycle.should_shutdown(now + timedelta(seconds=15), 15))

    def test_one_stale_tab_does_not_close_when_another_is_active(self):
        now = datetime.utcnow()
        lifecycle.state['had_sessions'] = True
        lifecycle.state['sessions'] = {
            'stale': now - timedelta(seconds=31),
            'active': now - timedelta(seconds=2),
        }
        self.assertEqual(['stale'], lifecycle.expire_stale_sessions(now, 30))
        self.assertIn('active', lifecycle.state['sessions'])
        self.assertIsNone(lifecycle.state['empty_since'])


if __name__ == '__main__':
    unittest.main()
