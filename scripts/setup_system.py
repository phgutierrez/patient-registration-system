"""Preparação idempotente e não destrutiva do banco e da configuração."""
from __future__ import annotations

import os
import secrets
import shutil
import sqlite3
import sys
from contextlib import closing
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def ensure_persistent_env() -> Path:
    env_path = ROOT / '.env'
    example = ROOT / '.env.example'
    if not env_path.exists():
        if not example.exists():
            raise FileNotFoundError('.env.example não encontrado.')
        shutil.copy2(example, env_path)

    lines = env_path.read_text(encoding='utf-8').splitlines()
    output = []
    found = False
    for line in lines:
        if line.startswith('SECRET_KEY='):
            found = True
            value = line.partition('=')[2].strip()
            output.append(line if value else f'SECRET_KEY={secrets.token_hex(32)}')
        else:
            output.append(line)
    if not found:
        output.append(f'SECRET_KEY={secrets.token_hex(32)}')
    env_path.write_text('\n'.join(output) + '\n', encoding='utf-8')
    return env_path


def database_path() -> Path:
    return ROOT / 'instance' / 'prontuario.db'


def check_database(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    with closing(sqlite3.connect(path)) as connection:
        result = connection.execute('PRAGMA quick_check').fetchone()
    if not result or result[0] != 'ok':
        raise RuntimeError(f'Banco de dados corrompido: {result[0] if result else "sem resposta"}')


def backup_database(path: Path) -> Path | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    backup_dir = ROOT / 'backup'
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    target = backup_dir / f'prontuario_{timestamp}.db'
    with closing(sqlite3.connect(path)) as source, closing(sqlite3.connect(target)) as destination:
        source.backup(destination)
    return target


def prepare_database(create_backup: bool = True) -> dict:
    ensure_persistent_env()
    path = database_path()
    path.parent.mkdir(exist_ok=True)
    check_database(path)
    backup = backup_database(path) if create_backup else None

    os.environ['INSTANCE_PATH'] = str(path.parent)
    os.environ['APP_DATA_DIR'] = str(ROOT)
    from flask_migrate import stamp
    from src.app import create_app
    from src.extensions import db
    from src.runtime_security import ensure_security_schema
    import src.models  # noqa: F401

    app = create_app()
    with app.app_context():
        db.create_all()
        ensure_security_schema(app)
        # O esquema é compatibilizado pela aplicação; o stamp registra o baseline
        # sem reaplicar migrações históricas sobre colunas já existentes.
        stamp(revision='head')

    from server import create_initial_data
    create_initial_data(app)
    check_database(path)
    return {'database': path, 'backup': backup}


def main() -> int:
    try:
        result = prepare_database()
        print(f"[OK] Banco preparado: {result['database']}")
        if result['backup']:
            print(f"[OK] Backup criado: {result['backup']}")
        else:
            print('[OK] Banco novo; backup anterior não era necessário.')
        return 0
    except Exception as exc:
        print(f'[ERRO] Preparação não concluída: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
