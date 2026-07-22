"""Link calendar outcomes to surgery requests.

Revision ID: 011_calendar_surgery_link
Revises: 010_local_access_source
"""
from alembic import op
import sqlalchemy as sa

revision = '011_calendar_surgery_link'
down_revision = '010_local_access_source'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column['name'] for column in inspector.get_columns('calendar_event_status')}
    if 'surgery_request_id' not in columns:
        with op.batch_alter_table('calendar_event_status') as batch:
            batch.add_column(sa.Column('surgery_request_id', sa.Integer(), nullable=True))
            batch.create_foreign_key(
                'fk_calendar_event_status_surgery_request',
                'surgery_requests',
                ['surgery_request_id'],
                ['id'],
            )
            batch.create_index(
                'ix_calendar_event_status_surgery_request_id',
                ['surgery_request_id'],
                unique=False,
            )
    surgery_columns = {
        column['name']: column
        for column in inspector.get_columns('surgery_requests')
    }
    if 'scheduled_event_id' in surgery_columns:
        with op.batch_alter_table('surgery_requests') as batch:
            batch.alter_column(
                'scheduled_event_id',
                existing_type=sa.String(255),
                type_=sa.String(500),
                existing_nullable=True,
            )


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column['name'] for column in inspector.get_columns('calendar_event_status')}
    if 'surgery_request_id' in columns:
        with op.batch_alter_table('calendar_event_status') as batch:
            batch.drop_index('ix_calendar_event_status_surgery_request_id')
            batch.drop_constraint('fk_calendar_event_status_surgery_request', type_='foreignkey')
            batch.drop_column('surgery_request_id')
    with op.batch_alter_table('surgery_requests') as batch:
        batch.alter_column(
            'scheduled_event_id',
            existing_type=sa.String(500),
            type_=sa.String(255),
            existing_nullable=True,
        )
