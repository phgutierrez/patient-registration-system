"""Add ETag and Last-Modified columns to calendar_cache

Revision ID: 006_add_conditional_get_support
Revises: 005_create_calendar_event_status
Create Date: 2026-02-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '006_add_conditional_get_support'
down_revision = '005_create_calendar_event_status'
branch_labels = None
depends_on = None


def upgrade():
    """Add ETag and Last-Modified columns for conditional GET support"""
    # Check if the table exists first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'calendar_cache' in inspector.get_table_names():
        # Add new columns for conditional GET
        with op.batch_alter_table('calendar_cache', schema=None) as batch_op:
            batch_op.add_column(sa.Column('etag', sa.String(255), nullable=True))
            batch_op.add_column(sa.Column('last_modified', sa.String(255), nullable=True))
    else:
        # Create the table if it doesn't exist
        op.create_table('calendar_cache',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('calendar_id', sa.String(255), nullable=False),
            sa.Column('fetched_at', sa.DateTime(), nullable=True),
            sa.Column('events_json', sa.Text(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('etag', sa.String(255), nullable=True),
            sa.Column('last_modified', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        
        op.create_index(op.f('ix_calendar_cache_calendar_id'), 'calendar_cache', ['calendar_id'], unique=True)


def downgrade():
    """Remove ETag and Last-Modified columns"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'calendar_cache' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('calendar_cache')]
        
        with op.batch_alter_table('calendar_cache', schema=None) as batch_op:
            if 'etag' in existing_columns:
                batch_op.drop_column('etag')
            if 'last_modified' in existing_columns:
                batch_op.drop_column('last_modified')