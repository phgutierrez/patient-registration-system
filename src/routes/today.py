"""Pacientes do dia: consultas do médico logado lidas da tabela Ocorrencias do Access."""
from __future__ import annotations

import logging
from datetime import date, datetime

from flask import Blueprint, flash, redirect, request, session, url_for
from flask_login import current_user, login_required

from src.extensions import db, limiter
from src.htmx_utils import render_page_or_partial
from src.models.patient import Patient
from src.models.specialty import Specialty
from src.runtime_security import scoped_patients_query
from src.services.access_patient_service import (
    DAY_CACHE_TTL, AccessLookupError, access_patient_service, build_access_config,
    doctor_name_matches,
)
from src.services.specialty_service import get_active_specialty

logger = logging.getLogger(__name__)
today_bp = Blueprint('today', __name__, url_prefix='/hoje')

TURNOS = {'manha': 'MANHA', 'tarde': 'TARDE', 'ambos': None}
_FIELD_LIMITS = {'nome': 100, 'prontuario': 20, 'nome_mae': 100, 'cns': 15, 'cidade': 100, 'endereco': 200, 'contato': 20}


def _access_config():
    specialty = Specialty.query.filter_by(slug='ortopedia', is_active=True).first()
    return build_access_config(specialty.settings if specialty else None)


def _default_turno(now: datetime | None = None) -> str:
    return 'manha' if (now or datetime.now()).hour < 12 else 'ambos'


def filter_doctor_schedule(rows, doctor_name, turno_key):
    """Filtra pelo médico e turno, ordena por quandoreg e numera as posições."""
    wanted_turno = TURNOS.get(turno_key)
    mine = [row for row in rows if doctor_name_matches(row.get('medico'), doctor_name)]
    filtered = [row for row in mine if not wanted_turno or row.get('turno') == wanted_turno]
    filtered.sort(key=lambda row: (
        row.get('quandoreg') is None,
        row.get('quandoreg') or datetime.max,
        (row.get('nome') or '').lower(),
    ))
    return mine, [dict(row, posicao=index) for index, row in enumerate(filtered, start=1)]


def _parse_birth_date(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    raw = str(value or '').strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%d/%m/%Y %H:%M:%S'):
        try:
            return datetime.strptime(raw[:19], fmt)
        except ValueError:
            continue
    return None


def _parse_sex(value) -> str:
    text = str(value or '').strip().upper()
    if text.startswith('F'):
        return 'F'
    if text.startswith('M'):
        return 'M'
    return ''


def patient_from_access(data: dict, prontuario: str, specialty_id=None) -> dict | None:
    """Converte um registro do Access em argumentos de Patient. None se faltar nome/nascimento."""
    nome = str(data.get('nome') or '').strip()
    birth = _parse_birth_date(data.get('data_nascimento'))
    if not nome or birth is None:
        return None
    values = {
        'nome': nome,
        'prontuario': str(prontuario).strip(),
        'nome_mae': str(data.get('nome_mae') or '').strip(),
        'cns': ''.join(ch for ch in str(data.get('cns') or '') if ch.isdigit()) or str(data.get('cns') or '').strip(),
        'cidade': str(data.get('cidade') or '').strip(),
        'endereco': str(data.get('endereco') or '').strip() or None,
        'contato': str(data.get('contato') or '').strip(),
    }
    for field, limit in _FIELD_LIMITS.items():
        if values.get(field):
            values[field] = values[field][:limit]
    values.update(
        data_nascimento=birth,
        sexo=_parse_sex(data.get('sexo')) or 'M',
        diagnostico='',
        cid='',
        specialty_id=specialty_id,
    )
    return values


@today_bp.route('', methods=['GET'])
@login_required
@limiter.limit('40 per minute')
def index():
    if not session.get('specialty_slug'):
        return redirect(url_for('auth.select_user'))
    turno = request.args.get('turno') or _default_turno()
    if turno not in TURNOS:
        turno = 'ambos'
    force = request.args.get('sync') == '1'
    doctor_name = (getattr(current_user, 'full_name', '') or '').strip()
    context = {
        'turno': turno, 'doctor_name': doctor_name, 'today': date.today(),
        'appointments': [], 'mine_total': 0, 'day_total': 0,
        'synced_at': None, 'error': None, 'refresh_seconds': DAY_CACHE_TTL,
        'counts': {'manha': 0, 'tarde': 0, 'ambos': 0},
    }
    try:
        result = access_patient_service.daily_appointments(_access_config(), date.today(), force=force)
        rows = result['rows']
        mine, appointments = filter_doctor_schedule(rows, doctor_name, turno)
        context.update(
            appointments=appointments, mine_total=len(mine), day_total=len(rows),
            synced_at=result['synced_at'],
            counts={
                'manha': sum(1 for row in mine if row.get('turno') == 'MANHA'),
                'tarde': sum(1 for row in mine if row.get('turno') == 'TARDE'),
                'ambos': len(mine),
            },
        )
    except ValueError:
        context['error'] = {'message': 'A configuração do banco Access é inválida.', 'hint': 'Solicite ao administrador que revise as Configurações.'}
    except AccessLookupError as exc:
        logger.warning('Pacientes do dia indisponíveis: %s', exc.code)
        context['error'] = {'message': exc.message, 'hint': exc.hint}
    return render_page_or_partial('today/index.html', 'today/_list.html', **context)


@today_bp.route('/solicitar-cirurgia', methods=['POST'])
@login_required
@limiter.limit('20 per minute')
def request_surgery_for():
    prontuario = str(request.form.get('prontuario') or '').strip()
    back = url_for('today.index', turno=request.form.get('turno') or None)
    if not prontuario or len(prontuario) > 20:
        flash('Prontuário inválido.', 'danger')
        return redirect(back)

    patient = scoped_patients_query(Patient.query).filter(Patient.prontuario == prontuario).first()
    if patient is None:
        try:
            result = access_patient_service.search(_access_config(), prontuario)
        except ValueError:
            flash('A configuração do banco Access é inválida.', 'danger')
            return redirect(back)
        except AccessLookupError as exc:
            flash(f'{exc.message} {exc.hint}'.strip(), 'danger')
            return redirect(back)
        if not result.get('found'):
            flash(f'Prontuário {prontuario} não foi localizado no cadastro do CPAM.', 'warning')
            return redirect(back)
        specialty = get_active_specialty()
        specialty_id = current_user.specialty_id or (specialty.id if specialty else None)
        values = patient_from_access(result['data'] or {}, prontuario, specialty_id)
        if values is None:
            flash('O cadastro no CPAM está incompleto (nome ou data de nascimento). Cadastre o paciente manualmente.', 'warning')
            return redirect(url_for('patients.new_patient'))
        patient = Patient(**values)
        try:
            db.session.add(patient)
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Falha ao importar paciente do Access')
            flash('Não foi possível adicionar o paciente ao sistema.', 'danger')
            return redirect(back)
        flash(f'Paciente {patient.nome} importado do CPAM. Complete diagnóstico e CID.', 'success')
    return redirect(url_for('surgery.request_surgery', patient_id=patient.id))
