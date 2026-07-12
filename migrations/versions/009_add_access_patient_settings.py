"""Add read-only Access patient lookup settings.

Revision ID: 009_add_access_settings
Revises: 008_keep_orthopedics_only
"""
from alembic import op
import sqlalchemy as sa

revision = '009_add_access_settings'
down_revision = '008_keep_orthopedics_only'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('specialty_settings') as batch:
        batch.add_column(sa.Column('access_host', sa.String(255), nullable=False, server_default='192.168.1.252'))
        batch.add_column(sa.Column('access_share_path', sa.String(500), nullable=False, server_default=r'naqh\AMBULATORIO_SERV'))
        batch.add_column(sa.Column('access_filename', sa.String(255), nullable=False, server_default='AMBULATORIO_SERV.accdb'))
        batch.add_column(sa.Column('access_enabled', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('specialty_settings') as batch:
        batch.drop_column('access_enabled')
        batch.drop_column('access_filename')
        batch.drop_column('access_share_path')
        batch.drop_column('access_host')
