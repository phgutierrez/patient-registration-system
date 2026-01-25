"""Create patient and surgery_requests tables

Revision ID: create_patient_tables
Revises: 7c790a63a956
Create Date: 2025-01-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_patient_tables'
down_revision = '7c790a63a956'
branch_labels = None
depends_on = None


def upgrade():
    # Create patient table
    op.create_table(
        'patient',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('prontuario', sa.String(length=20), nullable=False),
        sa.Column('data_nascimento', sa.DateTime(), nullable=False),
        sa.Column('sexo', sa.String(length=1), nullable=False),
        sa.Column('nome_mae', sa.String(length=100), nullable=False),
        sa.Column('cns', sa.String(length=15), nullable=False),
        sa.Column('cidade', sa.String(length=100), nullable=False),
        sa.Column('endereco', sa.String(length=200), nullable=True),
        sa.Column('estado', sa.String(length=2), nullable=True),
        sa.Column('contato', sa.String(length=20), nullable=False),
        sa.Column('diagnostico', sa.Text(), nullable=False),
        sa.Column('cid', sa.String(length=4), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create surgery_requests table
    op.create_table(
        'surgery_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('peso', sa.Float(), nullable=False),
        sa.Column('sinais_sintomas', sa.Text(), nullable=False),
        sa.Column('condicoes_justificativa', sa.Text(), nullable=False),
        sa.Column('resultados_diagnosticos', sa.Text(), nullable=False),
        sa.Column('procedimento_solicitado', sa.String(length=100), nullable=False),
        sa.Column('codigo_procedimento', sa.String(length=10), nullable=False),
        sa.Column('tipo_cirurgia', sa.String(length=10), nullable=False),
        sa.Column('data_cirurgia', sa.Date(), nullable=False),
        sa.Column('internar_antes', sa.Boolean(), nullable=True),
        sa.Column('hora_cirurgia', sa.Time(), nullable=False),
        sa.Column('assistente', sa.String(length=100), nullable=False),
        sa.Column('aparelhos_especiais', sa.Text(), nullable=True),
        sa.Column('reserva_sangue', sa.Boolean(), nullable=True),
        sa.Column('quantidade_sangue', sa.String(length=20), nullable=True),
        sa.Column('raio_x', sa.Boolean(), nullable=True),
        sa.Column('reserva_uti', sa.Boolean(), nullable=True),
        sa.Column('duracao_prevista', sa.String(length=20), nullable=False),
        sa.Column('evolucao_internacao', sa.Text(), nullable=True),
        sa.Column('prescricao_internacao', sa.Text(), nullable=True),
        sa.Column('exames_preop', sa.Text(), nullable=True),
        sa.Column('opme', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
    
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('surgery_requests')
    op.drop_table('patient')