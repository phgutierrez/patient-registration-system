"""Build portátil Windows 32-bit, onedir e com pós-validação obrigatória."""
from __future__ import annotations

import shutil
import os
import struct
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import PyInstaller.__main__


ROOT = Path(__file__).resolve().parent
ENTRYPOINT = ROOT / 'server.py'
BUILD_ROOT = ROOT / 'build' / 'pyinstaller32'
DIST_ROOT = ROOT / 'dist' / 'Sistema32bits'
APP_NAME = 'PatientRegistration'
BASELINE_FILES = 920
BASELINE_BYTES = 81_126_589

DATA_FILES = (
    (ROOT / 'src' / 'templates', 'src/templates'),
    (ROOT / 'src' / 'static' / 'css', 'src/static/css'),
    (ROOT / 'src' / 'static' / 'js', 'src/static/js'),
    (ROOT / 'src' / 'static' / 'vendor', 'src/static/vendor'),
    (ROOT / 'src' / 'static' / 'icon.ico', 'src/static'),
    (ROOT / 'src' / 'static' / 'logo ortoped.png', 'src/static'),
    (ROOT / 'src' / 'static' / 'Internacao.pdf', 'src/static'),
    (ROOT / 'src' / 'static' / 'REQUISIÇÃO HEMOCOMPONENTE.pdf', 'src/static'),
)

HIDDEN_IMPORTS = (
    'sqlalchemy.sql.default_comparator',
    'pymupdf',
    'pyodbc',
)

EXCLUDES = (
    'matplotlib', 'numpy', 'pandas', 'pytest', 'IPython', 'jupyter',
    'notebook', 'sphinx', 'tkinter', 'sqlalchemy.testing', 'mypy',
    'test', 'doctest', 'pydoc', 'lib2to3',
)


def assert_within_project(path: Path) -> Path:
    resolved = path.resolve()
    root = ROOT.resolve()
    if resolved == root or root not in resolved.parents:
        raise RuntimeError(f'Caminho de build fora do projeto: {resolved}')
    return resolved


def assert_prerequisites() -> None:
    if struct.calcsize('P') * 8 != 32:
        raise RuntimeError('Ative um Python 32-bit antes de executar este build.')
    required = [ENTRYPOINT, ROOT / 'requirements.txt', *(source for source, _ in DATA_FILES)]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError('Arquivos obrigatórios ausentes:\n- ' + '\n- '.join(missing))
    import pymupdf
    if not hasattr(pymupdf.Document, 'bake'):
        raise RuntimeError('A versão instalada do PyMuPDF não oferece Document.bake().')


def build_arguments(dist_root: Path, run_root: Path) -> list[str]:
    args = [
        str(ENTRYPOINT), '--onedir', '--noconsole', '--clean', '--noconfirm', '--noupx',
        '--python-option=O', f'--name={APP_NAME}', f'--distpath={dist_root}',
        f'--workpath={run_root / "work"}', f'--specpath={run_root / "spec"}',
        f'--icon={ROOT / "src" / "static" / "icon.ico"}',
        '--copy-metadata=flask', '--copy-metadata=flask-sqlalchemy',
        '--copy-metadata=flask-login', '--copy-metadata=flask-wtf',
        '--copy-metadata=waitress',
    ]
    for source, destination in DATA_FILES:
        args.append(f'--add-data={source};{destination}')
    for module in HIDDEN_IMPORTS:
        args.append(f'--hidden-import={module}')
    for module in EXCLUDES:
        args.append(f'--exclude-module={module}')
    return args


def validate_distribution(app_dir: Path) -> tuple[int, int]:
    executable = app_dir / f'{APP_NAME}.exe'
    required = (
        executable,
        app_dir / '_internal' / 'src' / 'templates',
        app_dir / '_internal' / 'src' / 'static' / 'vendor' / 'bootstrap' / 'bootstrap.min.css',
        app_dir / '_internal' / 'src' / 'static' / 'vendor' / 'bootstrap' / 'bootstrap.bundle.min.js',
        app_dir / '_internal' / 'src' / 'static' / 'Internacao.pdf',
        app_dir / '_internal' / 'src' / 'static' / 'REQUISIÇÃO HEMOCOMPONENTE.pdf',
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError('Distribuição incompleta:\n- ' + '\n- '.join(missing))

    forbidden = ('pandas', 'numpy', 'sqlalchemy/testing', 'static/pdfs/gerados')
    normalized_paths = [str(path.relative_to(app_dir)).replace('\\', '/').lower()
                        for path in app_dir.rglob('*')]
    found = [name for name in forbidden if any(name in path for path in normalized_paths)]
    if found:
        raise RuntimeError('Módulos/dados proibidos no build: ' + ', '.join(found))

    with tempfile.TemporaryDirectory(prefix='patient-registration-self-check-') as data_dir:
        environment = os.environ.copy()
        environment['PATIENT_REGISTRATION_NO_DIALOG'] = '1'
        try:
            completed = subprocess.run(
                [str(executable), '--self-check', '--no-browser', '--data-dir', data_dir],
                timeout=90, check=False, env=environment,
            )
        except subprocess.TimeoutExpired as exc:
            log_path = Path(data_dir) / 'logs' / 'patient-registration.log'
            detail = log_path.read_text(encoding='utf-8', errors='replace') if log_path.exists() else 'sem log'
            raise RuntimeError(f'Autoverificação excedeu o tempo limite:\n{detail[-4000:]}') from exc
        if completed.returncode != 0:
            log_path = Path(data_dir) / 'logs' / 'patient-registration.log'
            detail = log_path.read_text(encoding='utf-8', errors='replace') if log_path.exists() else 'sem log'
            raise RuntimeError(f'Autoverificação do executável falhou ({completed.returncode}):\n{detail[-4000:]}')

    files = [path for path in app_dir.rglob('*') if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def main() -> int:
    assert_prerequisites()
    run_stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    run_root = assert_within_project(BUILD_ROOT / 'runs' / run_stamp)
    run_root.mkdir(parents=True, exist_ok=True)
    dist_root = assert_within_project(DIST_ROOT)
    output = assert_within_project(dist_root / APP_NAME)
    if output.exists():
        try:
            shutil.rmtree(output)
        except OSError as exc:
            suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
            dist_root = assert_within_project(ROOT / 'dist' / f'Sistema32bits_novo_{suffix}')
            output = assert_within_project(dist_root / APP_NAME)
            print(f'[AVISO] Distribuição anterior está em uso ({exc}).')
            print(f'[AVISO] O novo build será criado em: {dist_root}')

    print(f'Build {APP_NAME}: Python {sys.version.split()[0]} ({struct.calcsize("P") * 8}-bit)')
    PyInstaller.__main__.run(build_arguments(dist_root, run_root))
    files, size = validate_distribution(output)
    print(f'[OK] Build validado: {files} arquivos, {size / 1024 / 1024:.2f} MiB')
    print(f'Baseline: {BASELINE_FILES} arquivos, {BASELINE_BYTES / 1024 / 1024:.2f} MiB')
    print(f'Redução: {BASELINE_FILES - files} arquivos, {(BASELINE_BYTES - size) / 1024 / 1024:.2f} MiB')
    print(f'Executável: {output / (APP_NAME + ".exe")}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f'[ERRO] Build não concluído: {exc}')
        raise SystemExit(1)
