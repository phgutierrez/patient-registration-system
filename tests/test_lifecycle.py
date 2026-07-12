import unittest

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


if __name__ == '__main__':
    unittest.main()
