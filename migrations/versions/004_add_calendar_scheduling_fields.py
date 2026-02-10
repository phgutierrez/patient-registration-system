"""add_calendar_scheduling_fields

Revision ID: 004_add_calendar_fields
Revises: 001_create_calendar_cache
Create Date: 2026-02-05 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_calendar_fields'
down_revision = '001_create_calendar_cache'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos de agendamento ao modelo SurgeryRequest
    with op.batch_alter_table('surgery_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scheduled_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('scheduled_event_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('scheduled_event_link', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('calendar_status', sa.String(length=20), nullable=True))


def downgrade():
    # Remover campos de agendamento
    with op.batch_alter_table('surgery_requests', schema=None) as batch_op:
        batch_op.drop_column('calendar_status')
        batch_op.drop_column('scheduled_event_link')
        batch_op.drop_column('scheduled_event_id')
        batch_op.drop_column('scheduled_at')
