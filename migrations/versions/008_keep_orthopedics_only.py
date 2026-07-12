"""Manter somente a especialidade Ortopedia.

Revision ID: 008_keep_orthopedics_only
Revises: 007_add_specialties
Create Date: 2026-07-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '008_keep_orthopedics_only'
down_revision = '007_add_specialties'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    ortopedia_id = bind.execute(
        sa.text("SELECT id FROM specialties WHERE slug = 'ortopedia' LIMIT 1")
    ).scalar()
    if ortopedia_id is None:
        bind.execute(sa.text(
            "INSERT INTO specialties (slug, name, is_active, created_at, updated_at) "
            "VALUES ('ortopedia', 'Ortopedia', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ))
        ortopedia_id = bind.execute(
            sa.text("SELECT id FROM specialties WHERE slug = 'ortopedia' LIMIT 1")
        ).scalar()

    tables = set(inspector.get_table_names())
    for table_name in ('users', 'surgery_requests', 'patient'):
        if table_name not in tables:
            continue
        columns = {column['name'] for column in inspector.get_columns(table_name)}
        if 'specialty_id' in columns:
            bind.execute(
                sa.text(f'UPDATE {table_name} SET specialty_id = :ortopedia_id'),
                {'ortopedia_id': ortopedia_id},
            )

    bind.execute(sa.text(
        'DELETE FROM specialty_procedures WHERE specialty_id <> :ortopedia_id'
    ), {'ortopedia_id': ortopedia_id})
    bind.execute(sa.text(
        'DELETE FROM specialty_settings WHERE specialty_id <> :ortopedia_id'
    ), {'ortopedia_id': ortopedia_id})
    bind.execute(sa.text(
        'DELETE FROM specialties WHERE id <> :ortopedia_id'
    ), {'ortopedia_id': ortopedia_id})


def downgrade():
    # A remoção é intencional e não recria especialidades fora do escopo.
    pass
