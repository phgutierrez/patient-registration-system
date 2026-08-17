"""Build portátil Windows 32-bit, onedir e com pós-validação obrigatória."""
from __future__ import annotations

import shutil
import hashlib
import json
import os
import struct
import subprocess
import sys
import sysconfig
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
GREENLET_WHEEL = ROOT / 'build_support' / 'greenlet-2.0.2-cp311-cp311-win32.whl'
GREENLET_WHEEL_SHA256 = 'e3c43e42f4bdf29cc18e569b4097f948c0547b0a81c78a291e29169315a3b941'
CRYPTO_WHEEL = ROOT / 'build_support' / 'pycryptodome-3.23.0-cp37-abi3-win32.whl'
CRYPTO_WHEEL_SHA256 = '507dbead45474b62b2bbe318eb1c4c8ee641077532067fec9c1aa82c31f84886'
BUILD_VERSION = '2.1.0-sync1'
LAST_BUILD_FILE = BUILD_ROOT.parent / 'last_build_32bits.txt'
NETWORK_LAUNCHER_FILES = (
    (ROOT / 'Iniciar_Sistema_Rede.bat', 'Iniciar_Sistema_Rede.bat'),
    (ROOT / 'launcher_network.ps1', 'launcher_network.ps1'),
    (ROOT / 'docs' / 'ACESSO_REDE_COPIA_LOCAL.md', 'LEIA-ME_ACESSO_REDE.txt'),
)

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
    'greenlet._greenlet',
    'pymupdf',
    'pyodbc',
    'Crypto',
    'Crypto.Cipher.AES',
    'Crypto.Cipher._mode_gcm',
    'Crypto.Hash.BLAKE2s',
)

EXCLUDES = (
    'matplotlib', 'numpy', 'pandas', 'pytest', 'IPython', 'jupyter',
    'notebook', 'sphinx', 'tkinter', 'sqlalchemy.testing', 'mypy',
    'test', 'doctest', 'pydoc', 'lib2to3', 'greenlet.tests',
)


def assert_within_project(path: Path) -> Path:
    resolved = path.resolve()
    root = ROOT.resolve()
    if resolved == root or root not in resolved.parents:
        raise RuntimeError(f'Caminho de build fora do projeto: {resolved}')
    return resolved


def assert_prerequisites() -> None:
    if sys.version_info[:2] != (3, 11) or struct.calcsize('P') * 8 != 32 or sysconfig.get_platform() != 'win32':
        raise RuntimeError('O build exige exatamente CPython 3.11 para Windows 32-bit (win32).')
    required = [
        ENTRYPOINT, ROOT / 'requirements.txt', GREENLET_WHEEL, CRYPTO_WHEEL,
        *(source for source, _ in DATA_FILES),
        *(source for source, _ in NETWORK_LAUNCHER_FILES),
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError('Arquivos obrigatórios ausentes:\n- ' + '\n- '.join(missing))
    wheels = ((GREENLET_WHEEL, GREENLET_WHEEL_SHA256, 'greenlet'),
              (CRYPTO_WHEEL, CRYPTO_WHEEL_SHA256, 'PyCryptodome'))
    for wheel, expected_hash, label in wheels:
        wheel_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if wheel_hash != expected_hash:
            raise RuntimeError(f'O wheel local do {label} falhou na verificação SHA-256.')
    from Crypto.Cipher import AES
    import Crypto
    import greenlet
    import pyodbc
    import sqlalchemy
    import pymupdf
    if Crypto.__version__ != '3.23.0' or AES.MODE_GCM != 11:
        raise RuntimeError('PyCryptodome/AES-GCM incompatível com o build.')
    if greenlet.__version__ != '2.0.2':
        raise RuntimeError(f'greenlet incompatível: esperado 2.0.2, encontrado {greenlet.__version__}.')
    if not str(greenlet._greenlet.__file__).lower().endswith('.pyd'):
        raise RuntimeError('A extensão binária win32 do greenlet não está carregada.')
    if not str(pyodbc.__file__).lower().endswith('.pyd'):
        raise RuntimeError('A extensão binária win32 do pyodbc não está carregada.')
    if not sqlalchemy.__version__.startswith('1.4.'):
        raise RuntimeError(f'SQLAlchemy incompatível com o build: {sqlalchemy.__version__}.')
    if not hasattr(pymupdf.Document, 'bake'):
        raise RuntimeError('A versão instalada do PyMuPDF não oferece Document.bake().')
    lifecycle_js = ROOT / 'src' / 'static' / 'js' / 'lifecycle.js'
    source = lifecycle_js.read_text(encoding='utf-8')
    if 'window.shutdownServer' not in source:
        raise RuntimeError('lifecycle.js não exporta window.shutdownServer.')
    node = shutil.which('node')
    if node:
        for script in sorted((ROOT / 'src' / 'static' / 'js').rglob('*.js')):
            checked = subprocess.run([node, '--check', str(script)], check=False)
            if checked.returncode != 0:
                raise RuntimeError(f'{script.name} contém erro de sintaxe.')
    else:
        required_markers = {
            'app-shell.js': 'sidebarPinned',
            'agenda.js': 'eventStatusForm',
            'patient-new.js': 'searchAccess',
            'surgery-request.js': 'cirurgiaModelos',
            'patients.js': 'data-delete-patient',
        }
        for name, marker in required_markers.items():
            page_script = ROOT / 'src' / 'static' / 'js' / 'pages' / name
            if marker not in page_script.read_text(encoding='utf-8'):
                raise RuntimeError(f'{name} falhou na validação estrutural.')

    powershell = shutil.which('powershell') or shutil.which('powershell.exe')
    if powershell:
        launcher = ROOT / 'launcher_network.ps1'
        launcher_arg = str(launcher).replace("'", "''")
        syntax_command = (
            '$errors=$null; '
            '[System.Management.Automation.Language.Parser]::ParseFile('
            f"'{launcher_arg}', [ref]$null, [ref]$errors) | Out-Null; "
            'if($errors.Count){'
            '$errors | ForEach-Object { Write-Error $_ }; exit 1}'
        )
        syntax_check = subprocess.run(
            [
                powershell, '-NoLogo', '-NoProfile', '-NonInteractive',
                '-Command', syntax_command,
            ],
            check=False,
        )
        if syntax_check.returncode != 0:
            raise RuntimeError('launcher_network.ps1 contém erro de sintaxe.')


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
        app_dir / 'build_manifest.json',
        app_dir / 'Iniciar_Sistema_Rede.bat',
        app_dir / 'launcher_network.ps1',
        app_dir / 'LEIA-ME_ACESSO_REDE.txt',
        app_dir / '_internal' / 'src' / 'templates',
        app_dir / '_internal' / 'src' / 'static' / 'js' / 'lifecycle.js',
        app_dir / '_internal' / 'src' / 'static' / 'js' / 'app-shell.js',
        app_dir / '_internal' / 'src' / 'static' / 'css' / 'app-shell.css',
        app_dir / '_internal' / 'src' / 'static' / 'js' / 'sync-status.js',
        app_dir / '_internal' / 'src' / 'static' / 'css' / 'sync-status.css',
        app_dir / '_internal' / 'src' / 'static' / 'vendor' / 'bootstrap' / 'bootstrap.min.css',
        app_dir / '_internal' / 'src' / 'static' / 'vendor' / 'bootstrap' / 'bootstrap.bundle.min.js',
        app_dir / '_internal' / 'src' / 'static' / 'vendor' / 'fontawesome' / 'css' / 'all.min.css',
        app_dir / '_internal' / 'src' / 'static' / 'vendor' / 'fontawesome' / 'webfonts' / 'fa-solid-900.woff2',
        app_dir / '_internal' / 'src' / 'static' / 'js' / 'pages' / 'agenda.js',
        app_dir / '_internal' / 'src' / 'static' / 'js' / 'pages' / 'patient-new.js',
        app_dir / '_internal' / 'src' / 'static' / 'css' / 'pages' / 'patient-new.css',
        app_dir / '_internal' / 'src' / 'static' / 'css' / 'pages' / 'patient-view.css',
        app_dir / '_internal' / 'src' / 'static' / 'js' / 'pages' / 'patient-view.js',
        app_dir / '_internal' / 'src' / 'static' / 'css' / 'pages' / 'procedures.css',
        app_dir / '_internal' / 'src' / 'static' / 'js' / 'pages' / 'procedures.js',
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

    powershell = shutil.which('powershell') or shutil.which('powershell.exe')
    if powershell:
        with tempfile.TemporaryDirectory(prefix='patient-registration-launcher-') as launcher_dir:
            launcher_root = Path(launcher_dir)
            completed = subprocess.run(
                [
                    powershell, '-NoLogo', '-NoProfile', '-NonInteractive',
                    '-ExecutionPolicy', 'Bypass', '-File',
                    str(app_dir / 'launcher_network.ps1'),
                    '-SourceRoot', str(app_dir),
                    '-LocalProductRoot', str(launcher_root / 'local'),
                    '-SharedDataRoot', str(launcher_root / 'shared'),
                    '-PrepareOnly',
                ],
                timeout=90,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    'Autoverificação do launcher de rede falhou '
                    f'({completed.returncode}).'
                )

    files = [path for path in app_dir.rglob('*') if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files)


def write_build_manifest(app_dir: Path) -> Path:
    executable = app_dir / f'{APP_NAME}.exe'
    payload = {
        'application': APP_NAME,
        'version': BUILD_VERSION,
        'architecture': 'win32',
        'python': '.'.join(map(str, sys.version_info[:3])),
        'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
        'generated_at': datetime.utcnow().isoformat() + 'Z',
    }
    path = app_dir / 'build_manifest.json'
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + '\n',
        encoding='utf-8',
    )
    return path


def copy_network_launcher_files(app_dir: Path) -> None:
    for source, destination in NETWORK_LAUNCHER_FILES:
        shutil.copy2(source, app_dir / destination)

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
    write_build_manifest(output)
    copy_network_launcher_files(output)
    files, size = validate_distribution(output)
    LAST_BUILD_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_BUILD_FILE.write_text(str(output / (APP_NAME + '.exe')) + '\n', encoding='utf-8')
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
