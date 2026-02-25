"""Criar tabelas de especialidades e atualizar users e surgery_requests

Revision ID: 007_add_specialties
Revises: 005_create_calendar_event_status
Create Date: 2026-02-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean, Text, DateTime
from datetime import datetime

revision = '007_add_specialties'
down_revision = '006_add_conditional_get_support'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Tabela specialties ──────────────────────────────────────────────
    op.create_table(
        'specialties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )

    # ── 2. Tabela specialty_settings ───────────────────────────────────────
    op.create_table(
        'specialty_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('specialty_id', sa.Integer(), nullable=False),
        sa.Column('agenda_url', sa.Text(), nullable=True),
        sa.Column('forms_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['specialty_id'], ['specialties.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('specialty_id'),
    )

    # ── 3. Tabela specialty_procedures ────────────────────────────────────
    op.create_table(
        'specialty_procedures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('specialty_id', sa.Integer(), nullable=False),
        sa.Column('descricao', sa.String(length=300), nullable=False),
        sa.Column('codigo_sus', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['specialty_id'], ['specialties.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── 4. FK specialty_id em users ────────────────────────────────────────
    op.add_column('users', sa.Column('specialty_id', sa.Integer(), nullable=True))
    try:
        op.create_foreign_key('fk_users_specialty', 'users', 'specialties', ['specialty_id'], ['id'])
    except Exception:
        pass  # SQLite não suporta ADD CONSTRAINT; ignora silenciosamente

    # ── 5. FK specialty_id em surgery_requests ─────────────────────────────
    op.add_column('surgery_requests', sa.Column('specialty_id', sa.Integer(), nullable=True))
    try:
        op.create_foreign_key('fk_surgery_requests_specialty', 'surgery_requests', 'specialties', ['specialty_id'], ['id'])
    except Exception:
        pass

    # ── 6. Seed: especialidades padrão ─────────────────────────────────────
    specialties_t = table('specialties',
        column('id', Integer),
        column('slug', String),
        column('name', String),
        column('is_active', Boolean),
        column('created_at', DateTime),
        column('updated_at', DateTime),
    )
    now = datetime.utcnow()
    op.bulk_insert(specialties_t, [
        {'id': 1, 'slug': 'ortopedia', 'name': 'Ortopedia', 'is_active': True, 'created_at': now, 'updated_at': now},
        {'id': 2, 'slug': 'cirurgia_pediatrica', 'name': 'Cirurgia Pediátrica', 'is_active': True, 'created_at': now, 'updated_at': now},
    ])

    # ── 7. Seed: configurações Ortopedia (links hardcoded extraídos do código) ──
    settings_t = table('specialty_settings',
        column('specialty_id', Integer),
        column('agenda_url', Text),
        column('forms_url', Text),
        column('created_at', DateTime),
        column('updated_at', DateTime),
    )
    op.bulk_insert(settings_t, [
        {
            'specialty_id': 1,
            # Link base do Google Forms de agendamento cirúrgico (Ortopedia)
            'forms_url': 'https://docs.google.com/forms/d/e/1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg/viewform',
            'agenda_url': '',  # Configurar via painel de settings
            'created_at': now,
            'updated_at': now,
        },
        {
            'specialty_id': 2,
            'forms_url': '',   # Preencher via painel de settings
            'agenda_url': '',
            'created_at': now,
            'updated_at': now,
        },
    ])

    # ── 8. Seed: procedimentos de Ortopedia (hardcoded → banco) ────────────
    procs_t = table('specialty_procedures',
        column('specialty_id', Integer),
        column('descricao', String),
        column('codigo_sus', String),
        column('is_active', Boolean),
        column('sort_order', Integer),
        column('created_at', DateTime),
        column('updated_at', DateTime),
    )
    ortopedia_procedures = [
        ('Epifisiodese femoral proximal in situ', '0408040130'),
        ('Osteotomia da Pelve', '0408040157'),
        ('Realinhamento do mecanismo extensor do joelho', '0408050128'),
        ('Redução Incruenta de Luxação congênita coxofemoral', '0408040181'),
        ('Revisão cirúrgica do Pé torto congênito', '0408050349'),
        ('Tratamento cirúrgico de luxação coxofemoral congenita', '0408040327'),
        ('Tratamento cirúrgico de luxação espontânea / progressiva / paralitica do quadril', '0408040343'),
        ('Talectomia', '0408050365'),
        ('Tratamento cirúrgico de coalizão tarsal', '0408050446'),
        ('Tratamento cirúrgico de pé cavo', '0408050730'),
        ('Tratamento cirúrgico de pé plano valgo', '0408050748'),
        ('Tratamento cirúrgico de pé torto congênito', '0408050764'),
        ('Tratamento cirúrgico de pé torto congênito inveterado', '0408050772'),
        ('Tratamento cirúrgico de pseudoartrose congênita da tibia', '0408050853'),
        ('Alongamento / Encurtamento miotendinoso', '0408060018'),
        ('Osteotomia de ossos longos exceto da mão e do pé', '0408060190'),
        ('Ressecção de cisto sinovial', '0408060212'),
        ('Retirada de fio ou pino intra-ósseo', '0408060352'),
        ('Retirada de Fixador externo', '0408060360'),
        ('Retirada de Placa e/ou parafusos', '0408060379'),
        ('Transposição / Transferência miotendinosa única', '0408060549'),
        ('Neurolise não funcional', '0403020077'),
    ]
    op.bulk_insert(procs_t, [
        {
            'specialty_id': 1, 'descricao': desc, 'codigo_sus': code,
            'is_active': True, 'sort_order': i,
            'created_at': now, 'updated_at': now,
        }
        for i, (desc, code) in enumerate(ortopedia_procedures)
    ])

    # ── 9. Atribuir especialidade Ortopedia a usuários existentes ──────────
    op.execute("UPDATE users SET specialty_id = 1 WHERE specialty_id IS NULL")


def downgrade():
    op.drop_column('surgery_requests', 'specialty_id')
    op.drop_column('users', 'specialty_id')
    op.drop_table('specialty_procedures')
    op.drop_table('specialty_settings')
    op.drop_table('specialties')
