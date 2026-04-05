"""One-shot migration: SQLite -> PostgreSQL (legacy-safe)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert

SOURCE_CANDIDATES = {
    'specialties': ['specialties'],
    'users': ['users'],
    'patients': ['patients', 'patient'],
    'surgery_requests': ['surgery_requests'],
    'calendar_cache': ['calendar_cache'],
    'calendar_event_status': ['calendar_event_status'],
}


def _find_source_table(conn: sqlite3.Connection, candidates: list[str]) -> str | None:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cur.fetchall()}
    for name in candidates:
        if name in existing:
            return name
    return None


def _rows_from_source(conn: sqlite3.Connection, table_name: str) -> list[sqlite3.Row]:
    cur = conn.execute(f'SELECT * FROM {table_name}')
    return cur.fetchall()


def migrate(sqlite_path: str, postgres_url: str) -> None:
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    pg_engine = create_engine(postgres_url)

    metadata = MetaData()
    metadata.reflect(bind=pg_engine)
    inspector = inspect(pg_engine)

    with pg_engine.begin() as pg_conn:
        for target_table, candidates in SOURCE_CANDIDATES.items():
            if not inspector.has_table(target_table):
                print(f'{target_table}: tabela destino inexistente, pulando')
                continue

            source_table = _find_source_table(sqlite_conn, candidates)
            if not source_table:
                print(f'{target_table}: tabela origem não encontrada, pulando')
                continue

            rows = _rows_from_source(sqlite_conn, source_table)
            if not rows:
                print(f'{target_table}: sem registros para migrar')
                continue

            table: Table = metadata.tables[target_table]
            allowed_columns = {col.name for col in table.columns}

            payload = []
            for row in rows:
                item = {k: row[k] for k in row.keys() if k in allowed_columns}
                if item:
                    payload.append(item)

            if not payload:
                print(f'{target_table}: nenhuma coluna compatível para migrar')
                continue

            stmt = pg_insert(table).values(payload).on_conflict_do_nothing()
            pg_conn.execute(stmt)
            print(f'{target_table}: {len(payload)} registros migrados (origem: {source_table})')

    sqlite_conn.close()


if __name__ == '__main__':
    sqlite_default = Path('instance') / 'prontuario.db'
    sqlite_path = os.getenv('SQLITE_PATH', str(sqlite_default))
    postgres_url = os.getenv('POSTGRES_SYNC_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/patient_registration')
    migrate(sqlite_path, postgres_url)
