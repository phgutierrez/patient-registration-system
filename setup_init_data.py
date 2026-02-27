"""
Script de inicializacao de dados chamado pelo setup_windows.bat.
Idempotente: cria especialidades, configuracoes, procedimentos e usuarios
apenas se nao existirem.
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.app import create_app
    from src.extensions import db
    from src.models.user import User
    from src.models.specialty import Specialty, SpecialtySettings, SpecialtyProcedure
    from sqlalchemy import inspect as sa_inspect
except ImportError as e:
    print(f"   [ERRO] Falha ao importar modulos: {e}")
    sys.exit(1)

app = create_app()

ORTOPEDIA_PROCEDURES = [
    ('Epifisiodese femoral proximal in situ',                                   '0408040130'),
    ('Osteotomia da Pelve',                                                     '0408040157'),
    ('Realinhamento do mecanismo extensor do joelho',                           '0408050128'),
    ('Reducao Incruenta de Luxacao congenita coxofemoral',                      '0408040181'),
    ('Revisao cirurgica do Pe torto congenito',                                 '0408050349'),
    ('Tratamento cirurgico de luxacao coxofemoral congenita',                   '0408040327'),
    ('Tratamento cirurgico de luxacao espontanea / progressiva / paralitica do quadril', '0408040343'),
    ('Talectomia',                                                              '0408050365'),
    ('Tratamento cirurgico de coalizao tarsal',                                 '0408050446'),
    ('Tratamento cirurgico de pe cavo',                                         '0408050730'),
    ('Tratamento cirurgico de pe plano valgo',                                  '0408050748'),
    ('Tratamento cirurgico de pe torto congenito',                              '0408050764'),
    ('Tratamento cirurgico de pe torto congenito inveterado',                   '0408050772'),
    ('Tratamento cirurgico de pseudoartrose congenita da tibia',                '0408050853'),
    ('Alongamento / Encurtamento miotendinoso',                                 '0408060018'),
    ('Osteotomia de ossos longos exceto da mao e do pe',                        '0408060190'),
    ('Resseccao de cisto sinovial',                                             '0408060212'),
    ('Retirada de fio ou pino intra-osseo',                                     '0408060352'),
    ('Retirada de Fixador externo',                                             '0408060360'),
    ('Retirada de Placa e/ou parafusos',                                        '0408060379'),
    ('Transposicao / Transferencia miotendinosa unica',                         '0408060549'),
    ('Neurolise nao funcional',                                                 '0403020077'),
]

with app.app_context():
    print("   - Verificando tabelas do banco de dados...")
    tables = sa_inspect(db.engine).get_table_names()

    for required in ('specialties', 'specialty_settings', 'specialty_procedures'):
        if required not in tables:
            print(f"   [ERRO] Tabela '{required}' nao encontrada!")
            print("          Execute: python create_tables_direct.py")
            sys.exit(1)

    print("   [OK] Tabelas verificadas")
    print()

    now = datetime.utcnow()
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 's4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com').strip()
    default_ortopedia_agenda_url = (
        os.getenv('ORTOPEDIA_AGENDA_URL')
        or os.getenv('GOOGLE_CALENDAR_ICS_URL')
        or (f'https://calendar.google.com/calendar/ical/{calendar_id}/public/basic.ics' if calendar_id else '')
    ).strip()

    # ── Especialidades ────────────────────────────────────────────────────
    print("   - Verificando especialidades...")
    spec_count = Specialty.query.count()
    if spec_count == 0:
        for slug, name in [('ortopedia', 'Ortopedia'), ('cirurgia_pediatrica', 'Cirurgia Pediatrica')]:
            db.session.add(Specialty(slug=slug, name=name, is_active=True, created_at=now, updated_at=now))
            print(f"       + {name}")
        db.session.flush()
        print("   [OK] Especialidades criadas")
    else:
        print(f"   [OK] {spec_count} especialidade(s) ja existem")

    print()

    # ── Configuracoes de especialidade ────────────────────────────────────
    print("   - Verificando configuracoes de especialidades...")
    ortopedia = Specialty.query.filter_by(slug='ortopedia').first()
    cirurgia  = Specialty.query.filter_by(slug='cirurgia_pediatrica').first()

    if ortopedia:
        ortopedia_settings = SpecialtySettings.query.filter_by(specialty_id=ortopedia.id).first()
        if not ortopedia_settings:
            db.session.add(SpecialtySettings(
                specialty_id=ortopedia.id,
                forms_url='https://docs.google.com/forms/d/e/1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg/viewform',
                agenda_url=default_ortopedia_agenda_url,
                created_at=now, updated_at=now,
            ))
            print("       + SpecialtySettings: Ortopedia (forms_url e agenda_url pre-configurados)")
        elif not (ortopedia_settings.agenda_url or '').strip() and default_ortopedia_agenda_url:
            ortopedia_settings.agenda_url = default_ortopedia_agenda_url
            ortopedia_settings.updated_at = now
            print("       + SpecialtySettings: Ortopedia agenda_url atualizado para valor padrão")

    if cirurgia and not SpecialtySettings.query.filter_by(specialty_id=cirurgia.id).first():
        db.session.add(SpecialtySettings(
            specialty_id=cirurgia.id,
            forms_url='',
            agenda_url='',
            created_at=now, updated_at=now,
        ))
        print("       + SpecialtySettings: Cirurgia Pediatrica")

    db.session.flush()
    print("   [OK] Configuracoes verificadas")
    print()

    # ── Procedimentos de Ortopedia ────────────────────────────────────────
    print("   - Verificando procedimentos de Ortopedia...")
    if ortopedia:
        proc_count = SpecialtyProcedure.query.filter_by(specialty_id=ortopedia.id).count()
        if proc_count == 0:
            for i, (desc, code) in enumerate(ORTOPEDIA_PROCEDURES):
                db.session.add(SpecialtyProcedure(
                    specialty_id=ortopedia.id,
                    descricao=desc, codigo_sus=code,
                    is_active=True, sort_order=i,
                    created_at=now, updated_at=now,
                ))
            db.session.flush()
            print(f"       + {len(ORTOPEDIA_PROCEDURES)} procedimentos de Ortopedia inseridos")
            print("   [OK] Procedimentos criados")
        else:
            print(f"   [OK] {proc_count} procedimento(s) de Ortopedia ja existem")
    else:
        print("   [AVISO] Ortopedia nao encontrada, pulando procedimentos")

    print()

    # ── Usuarios ──────────────────────────────────────────────────────────
    print("   - Verificando usuarios...")
    user_count = User.query.count()
    if user_count == 0:
        spec_id = ortopedia.id if ortopedia else 1
        for uname, fname in [
            ('pedro',   'Pedro Freitas'),
            ('andre',   'Andre Cristiano'),
            ('brauner', 'Brauner Cavalcanti'),
            ('savio',   'Savio Bruno'),
            ('laecio',  'Laecio Damaceno'),
        ]:
            db.session.add(User(
                username=uname, password='123456',
                full_name=fname, specialty_id=spec_id, role='solicitante'
            ))
            print(f"       + {uname} ({fname})")
        print("   [OK] Usuarios criados")
    else:
        print(f"   [OK] {user_count} usuario(s) ja existe(m)")

    db.session.commit()

    print()
    print("   [OK] Dados inicializados com sucesso!")
    print()
    print("   Resumo:")
    print(f"   - Especialidades:  {Specialty.query.count()}")
    print(f"   - Configuracoes:   {SpecialtySettings.query.count()}")
    print(f"   - Procedimentos:   {SpecialtyProcedure.query.count()}")
    print(f"   - Usuarios:        {User.query.count()}")
