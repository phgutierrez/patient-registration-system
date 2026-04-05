"""fastapi initial baseline

Revision ID: 001_fastapi_baseline
Revises:
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


revision = '001_fastapi_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'specialties',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(length=80), nullable=False, unique=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=80), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='enfermeiro'),
        sa.Column('full_name', sa.String(length=120), nullable=False),
        sa.Column('cns', sa.String(length=15), nullable=True),
        sa.Column('crm', sa.String(length=20), nullable=True),
        sa.Column('specialty_id', sa.Integer(), sa.ForeignKey('specialties.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('prontuario', sa.String(length=20), nullable=False),
        sa.Column('data_nascimento', sa.Date(), nullable=False),
        sa.Column('sexo', sa.String(length=1), nullable=False),
        sa.Column('nome_mae', sa.String(length=100), nullable=False),
        sa.Column('cns', sa.String(length=15), nullable=False),
        sa.Column('cidade', sa.String(length=100), nullable=False),
        sa.Column('endereco', sa.String(length=200), nullable=True),
        sa.Column('estado', sa.String(length=2), nullable=True),
        sa.Column('contato', sa.String(length=20), nullable=False),
        sa.Column('diagnostico', sa.Text(), nullable=False),
        sa.Column('cid', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'surgery_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('peso', sa.Float(), nullable=False),
        sa.Column('sinais_sintomas', sa.Text(), nullable=False),
        sa.Column('condicoes_justificativa', sa.Text(), nullable=False),
        sa.Column('resultados_diagnosticos', sa.Text(), nullable=False),
        sa.Column('procedimento_solicitado', sa.String(length=120), nullable=False),
        sa.Column('codigo_procedimento', sa.String(length=20), nullable=False),
        sa.Column('tipo_cirurgia', sa.String(length=20), nullable=False),
        sa.Column('data_cirurgia', sa.Date(), nullable=False),
        sa.Column('internar_antes', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('hora_cirurgia', sa.Time(), nullable=False),
        sa.Column('assistente', sa.String(length=120), nullable=False),
        sa.Column('aparelhos_especiais', sa.Text(), nullable=True),
        sa.Column('reserva_sangue', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('quantidade_sangue', sa.String(length=20), nullable=True),
        sa.Column('raio_x', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('reserva_uti', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('duracao_prevista', sa.String(length=30), nullable=False),
        sa.Column('evolucao_internacao', sa.Text(), nullable=True),
        sa.Column('prescricao_internacao', sa.Text(), nullable=True),
        sa.Column('exames_preop', sa.Text(), nullable=True),
        sa.Column('opme', sa.Text(), nullable=True),
        sa.Column('specialty_id', sa.Integer(), sa.ForeignKey('specialties.id'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='Pendente'),
        sa.Column('pdf_filename', sa.String(length=255), nullable=True),
        sa.Column('pdf_hemocomponente', sa.String(length=255), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('scheduled_event_id', sa.String(length=255), nullable=True),
        sa.Column('scheduled_event_link', sa.String(length=500), nullable=True),
        sa.Column('calendar_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'calendar_cache',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('calendar_id', sa.String(length=255), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=True),
        sa.Column('events_json', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('etag', sa.String(length=255), nullable=True),
        sa.Column('last_modified', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_calendar_cache_calendar_id', 'calendar_cache', ['calendar_id'], unique=True)

    op.create_table(
        'calendar_event_status',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_uid', sa.String(length=500), nullable=False, unique=True),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('suspension_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_calendar_event_status_event_date', 'calendar_event_status', ['event_date'])
    op.create_index('ix_calendar_event_status_event_uid', 'calendar_event_status', ['event_uid'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('audit_logs')
    op.drop_index('ix_calendar_event_status_event_uid', table_name='calendar_event_status')
    op.drop_index('ix_calendar_event_status_event_date', table_name='calendar_event_status')
    op.drop_table('calendar_event_status')
    op.drop_index('ix_calendar_cache_calendar_id', table_name='calendar_cache')
    op.drop_table('calendar_cache')
    op.drop_table('surgery_requests')
    op.drop_table('patients')
    op.drop_table('users')
    op.drop_table('specialties')
