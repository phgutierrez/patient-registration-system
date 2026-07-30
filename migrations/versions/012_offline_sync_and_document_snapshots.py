"""Add offline synchronization metadata and document snapshots.

Revision ID: 012_offline_sync
Revises: 011_calendar_surgery_link
"""
from alembic import op
import sqlalchemy as sa


revision = '012_offline_sync'
down_revision = '011_calendar_surgery_link'
branch_labels = None
depends_on = None


SYNC_TABLES = (
    'users',
    'patient',
    'surgery_requests',
    'specialties',
    'specialty_settings',
    'specialty_procedures',
    'calendar_event_status',
)


def _add_sync_columns(table_name: str) -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column['name'] for column in inspector.get_columns(table_name)}
    with op.batch_alter_table(table_name) as batch:
        if 'sync_uuid' not in columns:
            batch.add_column(sa.Column('sync_uuid', sa.String(36), nullable=True))
        if 'sync_field_versions' not in columns:
            batch.add_column(sa.Column(
                'sync_field_versions', sa.Text(), nullable=False, server_default='{}'
            ))
        if 'sync_deleted' not in columns:
            batch.add_column(sa.Column(
                'sync_deleted', sa.Boolean(), nullable=False, server_default=sa.false()
            ))
        if 'sync_updated_at' not in columns:
            batch.add_column(sa.Column(
                'sync_updated_at', sa.DateTime(), nullable=True
            ))


def upgrade():
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())
    for table_name in SYNC_TABLES:
        if table_name in existing:
            _add_sync_columns(table_name)

    if 'surgery_requests' in existing:
        surgery_columns = {
            column['name'] for column in inspector.get_columns('surgery_requests')
        }
        with op.batch_alter_table('surgery_requests') as batch:
            if 'scheduled_attempt_id' not in surgery_columns:
                batch.add_column(sa.Column(
                    'scheduled_attempt_id', sa.String(36), nullable=True
                ))
            if 'scheduled_result_uncertain' not in surgery_columns:
                batch.add_column(sa.Column(
                    'scheduled_result_uncertain', sa.Boolean(), nullable=False,
                    server_default=sa.false(),
                ))
    if 'patient' in existing:
        patient_columns = {
            column['name'] for column in inspector.get_columns('patient')
        }
        if 'superseded_by_uuid' not in patient_columns:
            with op.batch_alter_table('patient') as batch:
                batch.add_column(sa.Column(
                    'superseded_by_uuid', sa.String(36), nullable=True
                ))

    op.create_table(
        'device_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key', sa.String(100), nullable=False, unique=True),
        sa.Column('value_json', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'sync_outbox',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_uuid', sa.String(36), nullable=False, unique=True),
        sa.Column('event_order', sa.String(120), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_uuid', sa.String(36), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('publish_attempts', sa.Integer(), nullable=False),
        sa.Column('last_error', sa.String(500), nullable=True),
    )
    op.create_table(
        'sync_applied_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_uuid', sa.String(36), nullable=False, unique=True),
        sa.Column('source_device_uuid', sa.String(36), nullable=False),
        sa.Column('source_sequence', sa.Integer(), nullable=False),
        sa.Column('event_order', sa.String(120), nullable=False),
        sa.Column('applied_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'sync_device_state',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('device_uuid', sa.String(36), nullable=False, unique=True),
        sa.Column('last_published_sequence', sa.Integer(), nullable=False),
        sa.Column('last_published_hash', sa.String(64), nullable=True),
        sa.Column('last_consumed_sequence', sa.Integer(), nullable=False),
        sa.Column('last_consumed_hash', sa.String(64), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.String(500), nullable=True),
    )
    op.create_table(
        'sync_audit_revisions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_uuid', sa.String(36), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_uuid', sa.String(36), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('previous_value_json', sa.Text(), nullable=True),
        sa.Column('incoming_value_json', sa.Text(), nullable=True),
        sa.Column('previous_order', sa.String(120), nullable=True),
        sa.Column('incoming_order', sa.String(120), nullable=False),
        sa.Column('accepted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'document_template_archives',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_type', sa.String(40), nullable=False),
        sa.Column('template_id', sa.String(100), nullable=False),
        sa.Column('template_sha256', sa.String(64), nullable=False, unique=True),
        sa.Column('pdf_bytes', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('sync_uuid', sa.String(36), nullable=False, unique=True),
        sa.Column('sync_field_versions', sa.Text(), nullable=False),
        sa.Column('sync_deleted', sa.Boolean(), nullable=False),
        sa.Column('sync_updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'generated_document_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('surgery_request_id', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(40), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('output_filename', sa.String(255), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('template_id', sa.String(100), nullable=False),
        sa.Column('template_sha256', sa.String(64), nullable=False),
        sa.Column('renderer_version', sa.String(30), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('sync_uuid', sa.String(36), nullable=False, unique=True),
        sa.Column('sync_field_versions', sa.Text(), nullable=False),
        sa.Column('sync_deleted', sa.Boolean(), nullable=False),
        sa.Column('sync_updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['surgery_request_id'], ['surgery_requests.id']
        ),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
        sa.UniqueConstraint(
            'surgery_request_id', 'document_type', 'revision',
            name='uq_generated_document_revision',
        ),
    )


def downgrade():
    for table_name in (
        'generated_document_snapshots',
        'document_template_archives',
        'sync_audit_revisions',
        'sync_device_state',
        'sync_applied_events',
        'sync_outbox',
        'device_settings',
    ):
        op.drop_table(table_name)
