import socket
import unittest

from server import _port_is_available


class ServerStartupTests(unittest.TestCase):
    def test_port_conflict_is_detected(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(('127.0.0.1', 0))
            port = occupied.getsockname()[1]
            self.assertFalse(_port_is_available('127.0.0.1', port))

    def test_free_port_is_accepted(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        self.assertTrue(_port_is_available('127.0.0.1', port))


if __name__ == '__main__':
    unittest.main()
