"""Integração Vite/Jinja, fallback sem build, cache e restrições de CSP/CDN."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from src import frontend_assets
from tests import test_operational_ui_agenda as _base
from tests.frontend_helpers import load_manifest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'src' / 'templates'
STATIC = ROOT / 'src' / 'static'
ENTRIES = ROOT / 'frontend' / 'entries'

FAKE_MANIFEST = {
    'frontend/entries/agenda.js': {
        'file': 'js/agenda-AAAA1111.js', 'isEntry': True,
        'imports': ['_htmx-BBBB2222.js'], 'css': ['assets/agenda-CCCC3333.css'],
    },
    '_htmx-BBBB2222.js': {'file': 'js/chunks/htmx-BBBB2222.js', 'css': ['assets/htmx-DDDD4444.css']},
}


class _App(unittest.TestCase):
    setUp = _base.OperationalUiAgendaTests.setUp
    tearDown = _base.OperationalUiAgendaTests.tearDown
    _new_surgery = staticmethod(_base.OperationalUiAgendaTests._new_surgery)


class ManifestHelperTests(_App):
    def _with_static(self, manifest=None, icons=None):
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, folder)
        shutil.copy(STATIC / 'icon-map.json', folder / 'icon-map.json')
        if manifest is not None:
            (folder / 'dist' / '.vite').mkdir(parents=True)
            (folder / 'dist' / '.vite' / 'manifest.json').write_text(json.dumps(manifest))
        if icons is not None:
            (folder / 'icons').mkdir(exist_ok=True)
            (folder / 'icons' / 'icons-manifest.json').write_text(json.dumps(icons))
        self.app.static_folder = str(folder)

    def test_manifest_emits_hashed_css_js_and_preloads(self):
        self._with_static(FAKE_MANIFEST)
        with self.app.test_request_context():
            css = str(frontend_assets.vite_css('agenda'))
            js = str(frontend_assets.vite_js('agenda'))
        self.assertIn('/static/dist/assets/htmx-DDDD4444.css', css)
        self.assertIn('/static/dist/assets/agenda-CCCC3333.css', css)
        self.assertLess(css.index('htmx-DDDD4444'), css.index('agenda-CCCC3333'))
        self.assertIn('<link rel="modulepreload" href="/static/dist/js/chunks/htmx-BBBB2222.js">', js)
        self.assertIn('<script type="module" src="/static/dist/js/agenda-AAAA1111.js"></script>', js)

    def test_without_manifest_falls_back_to_source_files(self):
        self._with_static(None)
        with self.app.test_request_context():
            css = str(frontend_assets.vite_css('shell'))
            js = str(frontend_assets.vite_js('shell'))
            self.assertFalse(frontend_assets.frontend_bundles_available())
        self.assertIn('/static/css/app-shell.css', css)
        self.assertIn('<script defer src="/static/js/app-shell.js"></script>', js)
        self.assertIn('/static/js/lifecycle.js', js)

    def test_unknown_entry_is_an_error(self):
        with self.app.test_request_context(), self.assertRaises(KeyError):
            frontend_assets.vite_js('nao-existe')

    def test_icon_markup_uses_local_sprite(self):
        self._with_static(None, icons={'file': 'icons-0123abcd.svg', 'icons': ['search']})
        with self.app.test_request_context():
            plain = str(frontend_assets.icon('search', extra_class='me-2'))
            labelled = str(frontend_assets.icon('search', label='Buscar'))
            self.assertEqual('/static/icons/icons-0123abcd.svg', frontend_assets.icon_sprite_url())
            with self.assertRaises(KeyError):
                frontend_assets.icon('nao-mapeado')
        self.assertIn('<i class="lucide lucide-search me-2" aria-hidden="true">', plain)
        self.assertIn('<use href="/static/icons/icons-0123abcd.svg#search">', plain)
        self.assertIn('role="img" aria-label="Buscar"', labelled)

    def test_full_page_renders_with_fallback_when_bundles_missing(self):
        self._with_static(None)
        response = self.client.get('/patients/patients')
        self.assertEqual(200, response.status_code)
        self.assertIn(b'/static/js/pages/patients.js', response.data)
        self.assertIn(b'lucide-user-plus', response.data)


class ServedAssetsTests(_App):
    def test_hashed_dist_files_get_long_immutable_cache(self):
        manifest = load_manifest()
        if manifest is None:
            self.skipTest('Bundles não gerados (npm run build).')
        chunk = manifest['frontend/entries/shell.js']
        response = self.client.get(f"/static/dist/{chunk['file']}")
        self.assertEqual(200, response.status_code)
        cache = response.headers.get('Cache-Control', '')
        self.assertIn('max-age=31536000', cache)
        self.assertIn('immutable', cache)
        response.close()

        source = self.client.get('/static/js/app-shell.js')
        self.assertNotIn('max-age=31536000', source.headers.get('Cache-Control', ''))
        source.close()

    def test_precompressed_assets_served_when_gzip_accepted(self):
        import gzip
        path = '/static/vendor/bootstrap/bootstrap.min.css'
        plain = self.client.get(path)
        compressed = self.client.get(path, headers={'Accept-Encoding': 'gzip, deflate'})
        try:
            if not (STATIC / 'vendor' / 'bootstrap' / 'bootstrap.min.css.gz').is_file():
                self.skipTest('Arquivos .gz não gerados (npm run build).')
            self.assertNotIn('Content-Encoding', plain.headers)
            self.assertEqual('gzip', compressed.headers['Content-Encoding'])
            self.assertIn('text/css', compressed.headers['Content-Type'])
            self.assertIn('Accept-Encoding', compressed.headers['Vary'])
            self.assertLess(len(compressed.data), len(plain.data) / 3)
            self.assertEqual(plain.data, gzip.decompress(compressed.data))
        finally:
            plain.close()
            compressed.close()
        # Arquivos fora das pastas pré-comprimidas continuam iguais.
        pdf = self.client.get('/static/icon.ico', headers={'Accept-Encoding': 'gzip'})
        self.assertNotIn('Content-Encoding', pdf.headers)
        pdf.close()

    def test_bootstrap_js_only_on_pages_with_components(self):
        self.assertNotIn(b'bootstrap.bundle.min.js', self.client.get('/index').data)
        self.assertIn(b'bootstrap.bundle.min.js', self.client.get('/patients/patients').data)
        new_patient = self.client.get('/patients/patient/new').data
        self.assertNotIn(b'bootstrap.bundle.min.js', new_patient)

    def test_rendered_pages_do_not_reference_cdns(self):
        for url in ('/index', '/patients/patients', '/patients/patient/new', '/configuracoes/'):
            with self.subTest(url=url):
                html = self.client.get(url).get_data(as_text=True)
                for match in re.findall(r'(?:src|href)="([^"]+)"', html):
                    self.assertFalse(match.startswith(('http://', 'https://', '//')), match)


class SourceTreeTests(unittest.TestCase):
    def test_no_font_awesome_left(self):
        self.assertFalse((STATIC / 'vendor' / 'fontawesome').exists())
        pattern = re.compile(r'\bfa[sr]? fa-|\bfa-[a-z]')
        sources = [*TEMPLATES.rglob('*.html'), *(STATIC / 'js').rglob('*.js')]
        offenders = [str(path) for path in sources if pattern.search(path.read_text(encoding='utf-8'))]
        self.assertEqual([], offenders)

    def test_templates_have_no_inline_styles(self):
        for template in TEMPLATES.rglob('*.html'):
            source = template.read_text(encoding='utf-8')
            with self.subTest(template=str(template.relative_to(TEMPLATES))):
                self.assertNotIn('<style', source)
                self.assertIsNone(re.search(r'\sstyle=', source))

    def test_templates_have_no_executable_inline_scripts_or_handlers(self):
        inline_script = re.compile(r'<script(?![^>]*\bsrc=)(?![^>]*type="application/json")[^>]*>')
        handler = re.compile(r'\son(?:click|submit|change|load|input)=', re.IGNORECASE)
        for template in TEMPLATES.rglob('*.html'):
            source = template.read_text(encoding='utf-8')
            with self.subTest(template=str(template.relative_to(TEMPLATES))):
                self.assertIsNone(inline_script.search(source))
                self.assertIsNone(handler.search(source))

    def test_entries_and_fallbacks_are_consistent(self):
        entries = {path.stem for path in ENTRIES.glob('*.js')}
        self.assertEqual(entries, set(frontend_assets.LEGACY_ASSETS))
        for name, assets in frontend_assets.LEGACY_ASSETS.items():
            entry_source = (ENTRIES / f'{name}.js').read_text(encoding='utf-8')
            for path in assets['css'] + assets['js']:
                with self.subTest(entry=name, path=path):
                    self.assertTrue((STATIC / path).is_file())
                    self.assertIn(path, entry_source)

    def test_manifest_files_exist(self):
        manifest = load_manifest()
        if manifest is None:
            self.skipTest('Bundles não gerados (npm run build).')
        for name in frontend_assets.LEGACY_ASSETS:
            self.assertIn(f'frontend/entries/{name}.js', manifest)
        for chunk in manifest.values():
            for path in [chunk['file'], *chunk.get('css', ())]:
                self.assertTrue((STATIC / 'dist' / path).is_file(), path)
        icons = json.loads((STATIC / 'icons' / 'icons-manifest.json').read_text(encoding='utf-8'))
        self.assertTrue((STATIC / 'icons' / icons['file']).is_file())

    def test_template_icons_are_mapped_and_in_sprite(self):
        icon_map = json.loads((STATIC / 'icon-map.json').read_text(encoding='utf-8'))['icons']
        used = set()
        for template in TEMPLATES.rglob('*.html'):
            used.update(re.findall(r"icon\('([a-z0-9-]+)'", template.read_text(encoding='utf-8')))
        self.assertTrue(used)
        self.assertEqual(set(), used - set(icon_map))
        sprite_manifest = STATIC / 'icons' / 'icons-manifest.json'
        if sprite_manifest.is_file():
            sprite_icons = set(json.loads(sprite_manifest.read_text(encoding='utf-8'))['icons'])
            self.assertEqual(set(icon_map), sprite_icons)

    def test_csp_does_not_allow_inline_scripts(self):
        from src.config import Config
        policy = Config.SECURITY_CSP_REPORT_ONLY_POLICY
        script_src = re.search(r"script-src ([^;]+)", policy).group(1)
        self.assertNotIn("'unsafe-inline'", script_src)
        self.assertNotIn("'unsafe-eval'", script_src)
        style_src = re.search(r"style-src ([^;]+)", policy).group(1)
        self.assertNotIn("'unsafe-inline'", style_src)
        self.assertNotIn('https:', policy.split('connect-src')[0].split('frame-src')[0])
        self.assertTrue(Config.SECURITY_CSP_ENFORCE)


if __name__ == '__main__':
    unittest.main()
