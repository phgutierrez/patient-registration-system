"""Diagnóstico executável pelo cmd.exe, com códigos de saída confiáveis."""
from __future__ import annotations

import importlib.metadata
import os
import sqlite3
import struct
import sys
import tempfile
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED_PACKAGES = {
    'Flask': '3.1.3',
    'waitress': '3.0.2',
    'PyMuPDF': '1.28.0',
    'python-dotenv': '1.2.2',
}
REQUIRED_TEMPLATES = (
    ROOT / 'src' / 'static' / 'Internacao.pdf',
    ROOT / 'src' / 'static' / 'REQUISIÇÃO HEMOCOMPONENTE.pdf',
)


def ok(message):
    print(f'[OK] {message}')


def warn(message):
    print(f'[AVISO] {message}')


def fail(message):
    print(f'[ERRO] {message}')
    return False


def verify() -> bool:
    valid = True
    print(f'Python: {sys.version.split()[0]} ({struct.calcsize("P") * 8}-bit)')
    if sys.version_info < (3, 10):
        valid &= fail('Python 3.10 ou posterior é obrigatório.')
    else:
        ok('Versão do Python compatível.')

    for package, expected in REQUIRED_PACKAGES.items():
        try:
            installed = importlib.metadata.version(package)
            if installed != expected:
                valid &= fail(f'{package}: instalado {installed}, esperado {expected}.')
            else:
                ok(f'{package} {installed}')
        except importlib.metadata.PackageNotFoundError:
            valid &= fail(f'Dependência ausente: {package}')

    env_path = ROOT / '.env'
    if not env_path.exists():
        valid &= fail('.env não encontrado.')
    elif not any(line.startswith('SECRET_KEY=') and line.partition('=')[2].strip()
                 for line in env_path.read_text(encoding='utf-8').splitlines()):
        valid &= fail('SECRET_KEY persistente não configurada no .env.')
    else:
        ok('.env e SECRET_KEY persistente encontrados.')

    for template in REQUIRED_TEMPLATES:
        if template.is_file():
            ok(f'Modelo encontrado: {template.name}')
        else:
            valid &= fail(f'Modelo ausente: {template.name}')

    instance = ROOT / 'instance'
    try:
        instance.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=instance, delete=True):
            pass
        ok('Diretório instance permite escrita.')
    except OSError as exc:
        valid &= fail(f'Diretório instance sem escrita: {exc}')

    db_path = instance / 'prontuario.db'
    if not db_path.exists():
        valid &= fail('Banco não encontrado. Execute setup_windows.bat.')
        return valid
    try:
        with closing(sqlite3.connect(db_path)) as connection:
            check = connection.execute('PRAGMA quick_check').fetchone()[0]
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            access_columns = {
                row[1] for row in connection.execute('PRAGMA table_info(specialty_settings)')
            } if 'specialty_settings' in tables else set()
        if check != 'ok':
            valid &= fail(f'Integridade do banco falhou: {check}')
        required = {'users', 'specialties', 'specialty_settings', 'specialty_procedures', 'patient', 'surgery_requests'}
        missing = sorted(required - tables)
        if missing:
            valid &= fail('Tabelas ausentes: ' + ', '.join(missing))
        else:
            ok('Banco íntegro e tabelas obrigatórias presentes.')
        required_access_columns = {'access_host', 'access_share_path', 'access_filename', 'access_enabled'}
        missing_access_columns = sorted(required_access_columns - access_columns)
        if missing_access_columns:
            valid &= fail('Configuração Access incompleta: ' + ', '.join(missing_access_columns))
        else:
            ok('Configuração de consulta Access presente.')
    except sqlite3.Error as exc:
        valid &= fail(f'Não foi possível abrir o banco: {exc}')
        return valid

    os.environ['INSTANCE_PATH'] = str(instance)
    os.environ['APP_DATA_DIR'] = str(ROOT)
    try:
        from src.app import create_app
        from src.models.specialty import Specialty
        from src.models.user import User
        app = create_app()
        with app.app_context():
            ortopedia = Specialty.query.filter_by(slug='ortopedia', is_active=True).first()
            users = User.query.count()
            admins = User.query.filter_by(role='admin').count()
            if not ortopedia:
                valid &= fail('Ortopedia ativa não encontrada.')
            else:
                ok('Ortopedia ativa encontrada.')
            if users == 0:
                warn('Nenhum usuário: o assistente local será aberto no primeiro uso.')
            elif admins == 0:
                valid &= fail('Existem usuários, mas nenhum administrador. Use ADMIN_BOOTSTRAP_* para recuperação.')
            else:
                ok(f'{users} usuário(s), {admins} administrador(es).')
    except Exception as exc:
        valid &= fail(f'Importação da aplicação falhou: {exc}')
    return bool(valid)


if __name__ == '__main__':
    success = verify()
    print('\nRESULTADO: ' + ('APROVADO' if success else 'REPROVADO'))
    raise SystemExit(0 if success else 1)
