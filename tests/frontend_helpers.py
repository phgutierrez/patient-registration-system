"""Ajuda os testes a reconhecer os assets de uma entrada do frontend.

Com bundles gerados (src/static/dist/.vite/manifest.json) as páginas
referenciam arquivos com hash; sem eles, os arquivos-fonte (fallback).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'src' / 'static' / 'dist' / '.vite' / 'manifest.json'


def load_manifest():
    if not MANIFEST.is_file():
        return None
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def entry_asset_urls(name):
    """URLs (bytes) esperadas no HTML para a entrada ``name``."""
    from src.frontend_assets import LEGACY_ASSETS

    manifest = load_manifest()
    if manifest is None:
        files = LEGACY_ASSETS[name]['css'] + LEGACY_ASSETS[name]['js']
        return [f'/static/{path}'.encode() for path in files]
    chunk = manifest[f'frontend/entries/{name}.js']
    files = list(chunk.get('css', ())) + [chunk['file']]
    return [f'/static/dist/{path}'.encode() for path in files]
