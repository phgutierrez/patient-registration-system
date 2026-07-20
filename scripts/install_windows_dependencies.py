"""Instala dependências Windows exclusivamente a partir de wheels binários."""
from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / 'requirements.txt'
GREENLET_WHEEL = ROOT / 'build_support' / 'greenlet-2.0.2-cp311-cp311-win32.whl'
GREENLET_SHA256 = 'e3c43e42f4bdf29cc18e569b4097f948c0547b0a81c78a291e29169315a3b941'
PIP_LOG = ROOT / 'build' / 'setup_pip.log'


class DependencyInstallError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def interpreter_is_supported() -> bool:
    if sys.implementation.name != 'cpython' or sys.version_info[:2] < (3, 10):
        return False
    return not (platform.architecture()[0] == '32bit' and sys.version_info[:2] != (3, 11))


def classify_pip_failure(output: str) -> str:
    normalized = output.casefold()
    if any(marker in normalized for marker in (
        'no matching distribution found', 'could not find a version that satisfies',
        'is not a supported wheel on this platform',
    )):
        return 'BINARY_UNAVAILABLE'
    if any(marker in normalized for marker in (
        'connectionerror', 'newconnectionerror', 'read timed out', 'connect timeout',
        'temporary failure in name resolution', 'failed to establish a new connection',
    )):
        return 'NETWORK_ERROR'
    return 'PIP_ERROR'


def run_pip(arguments: list[str]) -> None:
    PIP_LOG.parent.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-m', 'pip', '--disable-pip-version-check',
               *arguments, '--log', str(PIP_LOG)]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    if result.returncode:
        code = classify_pip_failure(f'{result.stdout}\n{result.stderr}')
        messages = {
            'BINARY_UNAVAILABLE': ('Uma dependência não possui wheel para este Python. Use CPython 3.11; '
                                   'a compilação por Visual Build Tools permanecerá bloqueada.'),
            'NETWORK_ERROR': 'Não foi possível acessar o repositório de pacotes. Verifique a rede.',
            'PIP_ERROR': 'O pip não conseguiu concluir a instalação binária.',
        }
        raise DependencyInstallError(code, messages[code])


def validate_local_wheel() -> None:
    if not GREENLET_WHEEL.is_file():
        raise DependencyInstallError('WHEEL_MISSING', 'Wheel local do greenlet não encontrado.')
    actual = hashlib.sha256(GREENLET_WHEEL.read_bytes()).hexdigest()
    if actual != GREENLET_SHA256:
        raise DependencyInstallError('WHEEL_CORRUPT', 'SHA-256 do wheel local do greenlet é inválido.')


def validate_binary_imports() -> None:
    import greenlet
    import greenlet._greenlet as greenlet_binary
    import pymupdf
    import pyodbc
    import sqlalchemy

    if greenlet.__version__ != '2.0.2':
        raise DependencyInstallError('IMPORT_INVALID', 'Versão inesperada do greenlet instalada.')
    if not str(greenlet_binary.__file__).casefold().endswith('.pyd'):
        raise DependencyInstallError('IMPORT_INVALID', 'greenlet não foi carregado como binário Windows.')
    if not str(pyodbc.__file__).casefold().endswith('.pyd'):
        raise DependencyInstallError('IMPORT_INVALID', 'pyodbc não foi carregado como binário Windows.')
    if not hasattr(pymupdf.Document, 'bake') or not sqlalchemy.__version__:
        raise DependencyInstallError('IMPORT_INVALID', 'Dependências principais não passaram na validação.')


def install() -> None:
    if not interpreter_is_supported():
        raise DependencyInstallError('PYTHON_INCOMPATIBLE',
                                     'Python incompatível. Em Windows 32-bit use CPython 3.11.')
    if not REQUIREMENTS.is_file():
        raise DependencyInstallError('REQUIREMENTS_MISSING', 'requirements.txt não encontrado.')

    bits = platform.architecture()[0]
    print(f'Python {platform.python_version()} ({bits}); somente wheels binários serão aceitos.')
    if bits == '32bit' and sys.version_info[:2] == (3, 11):
        validate_local_wheel()
        run_pip(['install', '--no-deps', '--force-reinstall', str(GREENLET_WHEEL)])
    else:
        run_pip(['install', '--only-binary=:all:', 'greenlet==2.0.2'])

    run_pip(['install', '--only-binary=:all:', '-r', str(REQUIREMENTS)])
    run_pip(['check'])
    validate_binary_imports()
    print('[OK] Dependências binárias validadas; nenhum compilador foi utilizado.')


def main() -> int:
    try:
        install()
        return 0
    except DependencyInstallError as exc:
        print(f'[ERRO:{exc.code}] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
