"""Add mutually exclusive network/local Access source.

Revision ID: 010_local_access_source
Revises: 009_add_access_settings
"""
from alembic import op
import sqlalchemy as sa

revision = '010_local_access_source'
down_revision = '009_add_access_settings'
branch_labels = None
depends_on = None


def upgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('specialty_settings')}
    with op.batch_alter_table('specialty_settings') as batch:
        if 'access_source' not in existing:
            batch.add_column(sa.Column('access_source', sa.String(20), nullable=False, server_default='network'))
        if 'access_local_path' not in existing:
            batch.add_column(sa.Column('access_local_path', sa.Text(), nullable=True))


def downgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('specialty_settings')}
    with op.batch_alter_table('specialty_settings') as batch:
        if 'access_local_path' in existing:
            batch.drop_column('access_local_path')
        if 'access_source' in existing:
            batch.drop_column('access_source')
