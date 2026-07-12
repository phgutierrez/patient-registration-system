import unittest
from pathlib import Path

from src.app import create_app


class SecurityHeaderTests(unittest.TestCase):
    def test_regular_html_keeps_deny_frame_policy(self):
        class TestConfig:
            TESTING = True
            SECRET_KEY = 'test-secret'
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            WTF_CSRF_ENABLED = False
            SECURITY_HEADERS_ENABLED = True
            SECURITY_CSP_REPORT_ONLY = True
            SECURITY_CSP_REPORT_ONLY_POLICY = "default-src 'self'; frame-ancestors 'none'"
            SECURITY_CSP_REPORT_URI = ''
            SECURITY_HSTS_ENABLED = False
            RATELIMIT_ENABLED = False
            PROTECTED_PDF_DIR = '.'

        app = create_app(TestConfig)
        response = app.test_client().get('/health')
        self.assertEqual('DENY', response.headers['X-Frame-Options'])
        self.assertIn("frame-ancestors 'none'", response.headers['Content-Security-Policy-Report-Only'])

    def test_base_template_references_local_bootstrap(self):
        source = (Path(__file__).parents[1] / 'src' / 'templates' / 'base.html').read_text(encoding='utf-8')
        self.assertIn("vendor/bootstrap/bootstrap.min.css", source)
        self.assertIn("vendor/bootstrap/bootstrap.bundle.min.js", source)
        self.assertNotIn('cdn.jsdelivr.net/npm/bootstrap', source)


if __name__ == '__main__':
    unittest.main()
