"""add surgery fields

Revision ID: add_surgery_fields
Revises: 7c790a63a956
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_surgery_fields'
down_revision = 'create_patient_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona os novos campos para solicitação de cirurgia
    op.add_column('patient', sa.Column(
        'procedimento_solicitado', sa.String(200), nullable=True))
    op.add_column('patient', sa.Column(
        'cid_procedimento', sa.String(4), nullable=True))
    op.add_column('patient', sa.Column(
        'data_prevista_cirurgia', sa.DateTime(), nullable=True))
    op.add_column('patient', sa.Column(
        'observacoes', sa.Text(), nullable=True))


def downgrade():
    # Remove os campos adicionados
    op.drop_column('patient', 'procedimento_solicitado')
    op.drop_column('patient', 'cid_procedimento')
    op.drop_column('patient', 'data_prevista_cirurgia')
    op.drop_column('patient', 'observacoes')
