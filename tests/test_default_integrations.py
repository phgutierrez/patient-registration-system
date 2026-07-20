import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import dotenv_values

from server import ensure_env_file
from src.default_integrations import (
    DEFAULT_CALENDAR_ID, DEFAULT_CALENDAR_ICS_URL, DEFAULT_FORMS_EDIT_ID,
    DEFAULT_FORMS_PUBLIC_ID, DEFAULT_FORMS_VIEW_URL, PUBLIC_ENV_DEFAULTS,
    calendar_ics_url, forms_view_url,
)


INTEGRATION_KEYS = tuple(PUBLIC_ENV_DEFAULTS)


class DefaultIntegrationTests(unittest.TestCase):
    def clean_environment(self, values=None):
        environment = {key: '' for key in INTEGRATION_KEYS}
        environment.update(values or {})
        return patch.dict(os.environ, environment, clear=False)

    def test_public_urls_are_derived_from_local_ids(self):
        self.assertEqual(DEFAULT_CALENDAR_ICS_URL, calendar_ics_url(DEFAULT_CALENDAR_ID))
        self.assertIn('public/basic.ics', DEFAULT_CALENDAR_ICS_URL)
        self.assertEqual(DEFAULT_FORMS_VIEW_URL, forms_view_url(DEFAULT_FORMS_PUBLIC_ID))
        self.assertIn(DEFAULT_FORMS_PUBLIC_ID, DEFAULT_FORMS_VIEW_URL)

    def test_new_env_contains_defaults_without_copying_a_secret(self):
        with tempfile.TemporaryDirectory() as directory, self.clean_environment():
            ensure_env_file(directory)
            values = dotenv_values(Path(directory) / '.env')
        self.assertEqual(DEFAULT_CALENDAR_ID, values['GOOGLE_CALENDAR_ID'])
        self.assertEqual(DEFAULT_FORMS_PUBLIC_ID, values['GOOGLE_FORMS_PUBLIC_ID'])
        self.assertEqual(DEFAULT_FORMS_EDIT_ID, values['GOOGLE_FORMS_EDIT_ID'])
        self.assertEqual(DEFAULT_FORMS_VIEW_URL, values['GOOGLE_FORMS_VIEWFORM_URL'])
        self.assertTrue(values['SECRET_KEY'])

    def test_blank_integrations_are_filled_and_secret_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, self.clean_environment():
            env_path = Path(directory) / '.env'
            env_path.write_text('SECRET_KEY=keep-this-secret\nGOOGLE_CALENDAR_ID=\nGOOGLE_FORMS_PUBLIC_ID=\n', encoding='utf-8')
            ensure_env_file(directory)
            values = dotenv_values(env_path)
        self.assertEqual('keep-this-secret', values['SECRET_KEY'])
        self.assertEqual(DEFAULT_CALENDAR_ID, values['GOOGLE_CALENDAR_ID'])
        self.assertEqual(DEFAULT_FORMS_PUBLIC_ID, values['GOOGLE_FORMS_PUBLIC_ID'])

    def test_custom_file_and_process_values_have_priority(self):
        custom_form = 'custom-public-id'
        with tempfile.TemporaryDirectory() as directory, self.clean_environment({'GOOGLE_CALENDAR_ID': 'process-calendar'}):
            env_path = Path(directory) / '.env'
            env_path.write_text(f'SECRET_KEY=secret\nGOOGLE_CALENDAR_ID=\nGOOGLE_FORMS_PUBLIC_ID={custom_form}\n', encoding='utf-8')
            ensure_env_file(directory)
            values = dotenv_values(env_path)
        self.assertEqual('process-calendar', values['GOOGLE_CALENDAR_ID'])
        self.assertEqual(custom_form, values['GOOGLE_FORMS_PUBLIC_ID'])


class ManualShutdownJavascriptTests(unittest.TestCase):
    def test_script_exposes_only_manual_shutdown(self):
        root = Path(__file__).parents[1]
        source = (root / 'src' / 'static' / 'js' / 'lifecycle.js').read_text(encoding='utf-8')
        template = (root / 'src' / 'templates' / 'base.html').read_text(encoding='utf-8')
        self.assertIn('window.shutdownServer', source)
        self.assertIn("filename='js/lifecycle.js'", template)
        self.assertNotIn('async function shutdownServer(button)', template)
        self.assertNotIn('sendHeartbeat', source)
        self.assertNotIn('sendBeacon', source)
        self.assertNotIn('beforeunload', source)
        self.assertNotIn('data-heartbeat-url', template)
        self.assertNotIn('data-lifecycle-close-url', template)

    def test_backend_has_no_automatic_shutdown_monitor(self):
        root = Path(__file__).parents[1]
        app_source = (root / 'src' / 'app.py').read_text(encoding='utf-8')
        server_source = (root / 'server.py').read_text(encoding='utf-8')
        self.assertNotIn('start_monitor', app_source)
        self.assertNotIn('routes.lifecycle', app_source)
        self.assertNotIn('LIFECYCLE_SHUTDOWN_GRACE_SECONDS', server_source)


if __name__ == '__main__':
    unittest.main()
