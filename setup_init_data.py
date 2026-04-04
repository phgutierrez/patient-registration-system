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
    from src.services.default_seed_data import ORTOPEDIA_PROCEDURES
    from src.runtime_security import bootstrap_admin_if_configured
    from sqlalchemy import inspect as sa_inspect
except ImportError as e:
    print(f"   [ERRO] Falha ao importar modulos: {e}")
    sys.exit(1)

app = create_app()

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
    calendar_id = (os.getenv('GOOGLE_CALENDAR_ID') or '').strip()
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
                forms_url=(os.getenv('GOOGLE_FORMS_VIEWFORM_URL') or '').strip(),
                agenda_url=default_ortopedia_agenda_url,
                created_at=now, updated_at=now,
            ))
            print("       + SpecialtySettings: Ortopedia (agenda/forms a partir do ambiente, quando configurados)")
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
        print("   [OK] Nenhum usuario padrao inseguro sera criado")
    else:
        print(f"   [OK] {user_count} usuario(s) ja existe(m)")

    db.session.commit()
    bootstrap_admin_if_configured(app)

    print()
    print("   [OK] Dados inicializados com sucesso!")
    print()
    print("   Resumo:")
    print(f"   - Especialidades:  {Specialty.query.count()}")
    print(f"   - Configuracoes:   {SpecialtySettings.query.count()}")
    print(f"   - Procedimentos:   {SpecialtyProcedure.query.count()}")
    print(f"   - Usuarios:        {User.query.count()}")
