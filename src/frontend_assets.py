"""Integração Jinja com os bundles gerados pelo Vite (src/static/dist).

Uso nos templates:

    {% block page_styles %}{{ vite_css('agenda') }}{% endblock %}
    {% block page_scripts %}{{ vite_js('agenda') }}{% endblock %}
    {{ icon('search') }}

Quando ``src/static/dist/.vite/manifest.json`` não existe (ex.: checkout
sem ``npm run build``), os helpers emitem as tags dos arquivos-fonte em
``src/static/css`` e ``src/static/js`` — o sistema continua funcional, apenas
sem minificação, HTMX e Alpine (links e formulários seguem como GET/POST
tradicionais).
"""
from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path

from flask import current_app, url_for
from markupsafe import Markup, escape

logger = logging.getLogger(__name__)

MANIFEST_RELATIVE = Path('dist') / '.vite' / 'manifest.json'
ICONS_MANIFEST_RELATIVE = Path('dist') / 'icons-manifest.json'
ICON_MAP_RELATIVE = Path('icon-map.json')
HASHED_DIST_FILE = re.compile(r'^dist/.+-[A-Za-z0-9_-]{8,}\.[a-z0-9]+$')

# Arquivos-fonte equivalentes a cada entrada do Vite (fallback sem build).
LEGACY_ASSETS: dict[str, dict[str, tuple[str, ...]]] = {
    'shell': {
        'css': ('css/app-shell.css', 'css/sync-status.css'),
        'js': ('js/app-shell.js', 'js/sync-status.js', 'js/lifecycle.js'),
    },
    'patients': {'css': ('css/pages/patients.css',), 'js': ('js/pages/patients.js',)},
    'agenda': {'css': ('css/pages/agenda.css',), 'js': ('js/pages/agenda.js',)},
    'patient-new': {'css': ('css/pages/patient-new.css',), 'js': ('js/pages/patient-new.js',)},
    'patient-edit': {'css': ('css/pages/patient-edit.css',), 'js': ('js/pages/patient-edit.js',)},
    'surgery-request': {
        'css': ('css/pages/surgery-request.css',),
        'js': ('js/pages/surgery-request.js',),
    },
    'surgery-confirmation': {
        'css': ('css/pages/surgery-confirmation.css',),
        'js': ('js/pages/surgery-confirmation.js',),
    },
    'settings': {
        'css': ('css/pages/specialty-settings.css',),
        'js': ('js/pages/specialty-settings.js',),
    },
    'procedures': {'css': ('css/pages/procedures.css',), 'js': ('js/pages/procedures.js',)},
}

_lock = threading.Lock()
_cache: dict[str, tuple[float, object]] = {}


def _static_path(relative: Path) -> Path:
    return Path(current_app.static_folder) / relative


def _load_json(relative: Path):
    """Lê JSON do static com cache invalidado pela data de modificação."""
    path = _static_path(relative)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    key = str(path)
    with _lock:
        cached = _cache.get(key)
        if cached and cached[0] == mtime:
            return cached[1]
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        logger.exception('Manifesto de assets inválido: %s', path)
        return None
    with _lock:
        _cache[key] = (mtime, data)
    return data


def load_manifest():
    return _load_json(MANIFEST_RELATIVE)


def _entry_key(name: str) -> str:
    return f'frontend/entries/{name}.js'


def _static_url(filename: str) -> str:
    return url_for('static', filename=filename)


def _collect_css(manifest: dict, key: str, seen: set) -> list[str]:
    if key in seen or key not in manifest:
        return []
    seen.add(key)
    chunk = manifest[key]
    files: list[str] = []
    for imported in chunk.get('imports', ()):
        files.extend(_collect_css(manifest, imported, seen))
    files.extend(chunk.get('css', ()))
    return files


def _require_entry(name: str):
    if name not in LEGACY_ASSETS:
        raise KeyError(f'Entrada de frontend desconhecida: {name}')
    manifest = load_manifest()
    if manifest is None:
        return None
    chunk = manifest.get(_entry_key(name))
    if chunk is None:
        logger.warning('Entrada %s ausente do manifesto do Vite; usando fontes.', name)
    return chunk and manifest


def vite_css(name: str) -> Markup:
    manifest = _require_entry(name)
    if manifest is None:
        files = [_static_url(path) for path in LEGACY_ASSETS[name]['css']]
    else:
        unique = dict.fromkeys(_collect_css(manifest, _entry_key(name), set()))
        files = [_static_url(f'dist/{path}') for path in unique]
    return Markup(''.join(
        f'<link rel="stylesheet" href="{escape(href)}">' for href in files
    ))


def vite_js(name: str) -> Markup:
    manifest = _require_entry(name)
    if manifest is None:
        return Markup(''.join(
            f'<script defer src="{escape(_static_url(path))}"></script>'
            for path in LEGACY_ASSETS[name]['js']
        ))
    chunk = manifest[_entry_key(name)]
    tags = [
        f'<link rel="modulepreload" href="{escape(_static_url("dist/" + manifest[key]["file"]))}">'
        for key in chunk.get('imports', ()) if key in manifest
    ]
    tags.append(
        f'<script type="module" src="{escape(_static_url("dist/" + chunk["file"]))}"></script>'
    )
    return Markup(''.join(tags))


def frontend_bundles_available() -> bool:
    return load_manifest() is not None


def _icon_map() -> dict:
    data = _load_json(ICON_MAP_RELATIVE) or {}
    return data.get('icons', {})


def icon(name: str, label: str | None = None, extra_class: str = '') -> Markup:
    """Ícone Lucide via sprite SVG local (funciona sem JavaScript).

    Sem o sprite gerado, recorre ao Font Awesome equivalente do icon-map.
    """
    icons = _icon_map()
    if name not in icons:
        raise KeyError(f'Ícone não mapeado em icon-map.json: {name}')
    classes = f'icon icon-{name} {extra_class}'.strip()
    a11y = (
        f'role="img" aria-label="{escape(label)}"' if label else 'aria-hidden="true"'
    )
    sprite = _load_json(ICONS_MANIFEST_RELATIVE)
    if not sprite or name not in sprite.get('icons', ()):
        return Markup(
            f'<i class="fas fa-{escape(icons[name])} {escape(extra_class)}" {a11y}></i>'
        )
    href = _static_url(f'dist/{sprite["file"]}') + f'#{name}'
    return Markup(
        f'<svg class="{escape(classes)}" {a11y} focusable="false">'
        f'<use href="{escape(href)}"></use></svg>'
    )


def static_max_age(filename: str | None):
    """Cache longo apenas para arquivos versionados por hash em dist/."""
    if filename and HASHED_DIST_FILE.match(filename.replace('\\', '/')):
        return 31536000
    return None


def init_app(app) -> None:
    app.jinja_env.globals.update(
        vite_css=vite_css,
        vite_js=vite_js,
        icon=icon,
        frontend_bundles_available=frontend_bundles_available,
    )
    if not frontend_bundles_available_for(app):
        app.logger.warning(
            'Bundles do frontend ausentes (src/static/dist). Usando arquivos-fonte; '
            'execute "npm ci && npm run build" para gerar os bundles.'
        )


def frontend_bundles_available_for(app) -> bool:
    return (Path(app.static_folder) / MANIFEST_RELATIVE).is_file()
