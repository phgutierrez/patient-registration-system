from __future__ import annotations

import calendar as calendar_module
import logging
import re
from datetime import date, datetime, timedelta

from flask import (
    Blueprint, current_app, flash, jsonify, redirect, render_template,
    request, session, url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from src.extensions import db, limiter
from src.models.patient import Patient
from src.models.specialty import Specialty
from src.models.surgery_request import SurgeryRequest
from src.runtime_security import (
    require_admin, scoped_patients_query,
)
from src.services.specialty_service import (
    get_active_specialty, get_active_specialty_slug, get_specialty_settings,
    set_active_specialty_slug,
)

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)
_REQUEST_REFERENCE_RE = re.compile(r'\[SOLICITACAO:(\d+)\]', re.IGNORECASE)


def _active_specialty_patient_query():
    specialty = get_active_specialty()
    query = scoped_patients_query(Patient.query)
    if specialty:
        query = query.filter(Patient.specialty_id == specialty.id)
    return query


def _active_specialty_surgery_query():
    specialty = get_active_specialty()
    query = SurgeryRequest.query.outerjoin(
        Patient,
        SurgeryRequest.patient_id == Patient.id,
    )
    if specialty:
        query = query.filter(or_(
            SurgeryRequest.specialty_id == specialty.id,
            (
                SurgeryRequest.specialty_id.is_(None)
                & (Patient.specialty_id == specialty.id)
            ),
        ))
    elif not current_user.is_admin:
        query = query.filter(False)
    return query


@main.route('/')
@main.route('/index')
@login_required
def index():
    """Compact operational dashboard backed only by the local database."""
    if not session.get('specialty_slug'):
        return redirect(url_for('auth.select_user'))

    today = date.today()
    patient_query = _active_specialty_patient_query()
    surgery_query = _active_specialty_surgery_query()

    dashboard = {
        'patients': patient_query.count(),
        'pending': surgery_query.filter(
            func.lower(func.coalesce(SurgeryRequest.status, 'pendente')) == 'pendente'
        ).count(),
        'scheduled': surgery_query.filter(
            func.lower(func.coalesce(SurgeryRequest.calendar_status, '')) == 'agendado'
        ).count(),
    }
    upcoming = (
        surgery_query.options(joinedload(SurgeryRequest.patient))
        .filter(SurgeryRequest.data_cirurgia >= today)
        .filter(
            func.lower(func.coalesce(SurgeryRequest.status, 'pendente')).notin_(
                {'realizada', 'suspensa'}
            )
        )
        .order_by(
            SurgeryRequest.data_cirurgia.asc(),
            SurgeryRequest.hora_cirurgia.asc(),
            SurgeryRequest.id.asc(),
        )
        .limit(5)
        .all()
    )
    return render_template(
        'index.html',
        specialty=get_active_specialty(),
        dashboard=dashboard,
        upcoming=upcoming,
    )


@main.route('/select-specialty', methods=['POST'])
@login_required
def select_specialty():
    slug = request.form.get('specialty_slug', '').strip()
    specialty = (
        Specialty.query.filter_by(slug='ortopedia', is_active=True).first()
        if slug == 'ortopedia'
        else None
    )
    if not specialty:
        flash('Especialidade inválida.', 'error')
        return redirect(url_for('main.index'))
    if (
        not current_user.is_admin
        and current_user.specialty_id
        and current_user.specialty_id != specialty.id
    ):
        flash('Você só pode acessar a especialidade vinculada ao seu usuário.', 'error')
        return redirect(url_for('main.index'))
    set_active_specialty_slug(slug)
    flash(f'Especialidade ativa: {specialty.name}', 'success')
    return redirect(url_for('main.index'))


@main.route('/change-specialty')
def change_specialty():
    from flask_login import logout_user
    if current_user.is_authenticated:
        logout_user()
    session.pop('specialty_slug', None)
    return redirect(url_for('auth.select_user'))


@main.route('/shutdown', methods=['POST'])
def shutdown():
    if (
        not current_app.config.get('DESKTOP_MODE', False)
        or request.remote_addr not in {'127.0.0.1', '::1'}
    ):
        return jsonify({
            'success': False,
            'error': 'Desligamento disponível somente no modo local.',
        }), 403
    from src.services.auth_session import clear_authentication_session
    from src.services.server_control import server_controller
    clear_authentication_session(preserve_specialty=True)
    requested = server_controller.request_shutdown('browser-button')
    status = server_controller.status()
    if requested or status['state'] == 'stopping':
        return jsonify({
            'success': True,
            'message': 'Servidor sendo encerrado...',
            **status,
        }), 202
    return jsonify({
        'success': False,
        'error': 'Controlador do servidor indisponível.',
        **status,
    }), 503


@main.route('/shutdown/status', methods=['GET'])
def shutdown_status():
    if (
        not current_app.config.get('DESKTOP_MODE', False)
        or request.remote_addr not in {'127.0.0.1', '::1'}
    ):
        return jsonify({
            'error': 'Operação disponível somente no modo local.',
        }), 403
    from src.services.server_control import server_controller
    return jsonify(server_controller.status()), 200


def _calendar_context():
    from src.services.calendar_cache_service import get_calendar_cache_service

    specialty = get_active_specialty()
    settings = get_specialty_settings(specialty) if specialty else None
    if not specialty or not settings or not settings.agenda_url:
        return specialty, settings, None
    timezone = current_app.config.get(
        'GOOGLE_CALENDAR_TZ',
        'America/Fortaleza',
    )
    service = get_calendar_cache_service(
        calendar_id=f'specialty_{specialty.id}',
        ics_url=settings.agenda_url,
        timezone_str=timezone,
    )
    return specialty, settings, service


def _event_local_date(event):
    if event.get('all_day') and event.get('start_date'):
        return event['start_date']
    return event['start'].date()


def _parse_agenda_range(view, today):
    if view == 'month':
        month_value = request.args.get('month', '').strip()
        try:
            year, month = map(int, month_value.split('-'))
            first = date(year, month, 1)
        except (TypeError, ValueError):
            first = today.replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return first, last

    start_value = request.args.get('start', '').strip()
    end_value = request.args.get('end', '').strip()
    try:
        start = datetime.fromisoformat(start_value).date()
        end = datetime.fromisoformat(end_value).date()
        if end < start or (end - start).days > 62:
            raise ValueError
        return start, end
    except (TypeError, ValueError):
        return today, today + timedelta(days=6)


def _build_month_weeks(start_date, end_date, grouped, today):
    cells = []
    first_weekday = (start_date.weekday() + 1) % 7
    for _ in range(first_weekday):
        cells.append({
            'date': None, 'day': None, 'events': [],
            'is_other_month': True, 'is_today': False,
        })
    for day_number in range(1, end_date.day + 1):
        current = date(start_date.year, start_date.month, day_number)
        cells.append({
            'date': current,
            'day': day_number,
            'events': grouped.get(current.isoformat(), []),
            'is_other_month': False,
            'is_today': current == today,
        })
    while len(cells) % 7:
        cells.append({
            'date': None, 'day': None, 'events': [],
            'is_other_month': True, 'is_today': False,
        })
    return [cells[index:index + 7] for index in range(0, len(cells), 7)]


@main.route('/agenda')
@login_required
def agenda():
    specialty, settings, cache_service = _calendar_context()
    if cache_service is None:
        return render_template(
            'agenda.html',
            error='Agenda não configurada. O administrador deve informar o link nas Configurações.',
            error_type='not_configured',
            specialty=specialty,
            view='week',
            grouped_events={},
            sorted_dates=[],
            total_events=0,
            meta_source='error',
            weeks=[],
        ), 400

    preference_key = f'agenda_view_{current_user.id}_{specialty.id}'
    requested_view = request.args.get('view', '').strip().lower()
    if requested_view in {'week', 'month'}:
        view = requested_view
        session[preference_key] = view
    else:
        view = session.get(preference_key, 'week')
        if view not in {'week', 'month'}:
            view = 'week'

    status_filter = request.args.get('status', 'todos').strip().lower()
    if status_filter not in {'todos', 'pendente', 'realizada', 'suspensa'}:
        status_filter = 'todos'
    query_text = request.args.get('q', '').strip()[:100]
    today = date.today()
    start_date, end_date = _parse_agenda_range(view, today)

    calendar_data = cache_service.get_calendar_data()
    events = cache_service.calendar_service.filter_events(
        calendar_data.events,
        start_date,
        end_date,
        query_text or None,
    )

    from src.models.calendar_event_status import CalendarEventStatus
    event_uids = {event.get('uid') for event in events if event.get('uid')}
    status_map = {}
    if event_uids:
        for event_status in CalendarEventStatus.query.filter(
            CalendarEventStatus.event_uid.in_(event_uids)
        ).all():
            status_map[event_status.event_uid] = event_status

    filtered_events = []
    for event in events:
        saved = status_map.get(event.get('uid'))
        event['status'] = saved.status if saved else 'PENDENTE'
        event['suspension_reason'] = saved.suspension_reason if saved else None
        event['surgery_request_id'] = saved.surgery_request_id if saved else None
        event['event_date'] = _event_local_date(event).isoformat()
        if status_filter != 'todos' and event['status'].lower() != status_filter:
            continue
        filtered_events.append(event)

    grouped = cache_service.calendar_service.group_events_by_day(filtered_events)
    sorted_dates = sorted(grouped)
    formatted_dates = {
        key: cache_service.calendar_service.format_date(
            datetime.fromisoformat(key).date()
        )
        for key in sorted_dates
    }

    weeks = (
        _build_month_weeks(start_date, end_date, grouped, today)
        if view == 'month'
        else []
    )
    month_names = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
    ]
    age_seconds = max(
        0,
        (datetime.utcnow() - calendar_data.fetched_at).total_seconds(),
    )
    error = (
        calendar_data.last_error
        if calendar_data.source_status == 'error'
        else None
    )
    return render_template(
        'agenda.html',
        view=view,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        query=query_text,
        status_filter=status_filter,
        grouped_events=grouped,
        sorted_dates=sorted_dates,
        formatted_dates=formatted_dates,
        meta_source=calendar_data.source_status,
        error=error,
        specialty=specialty,
        total_events=len(filtered_events),
        weeks=weeks,
        month_name=month_names[start_date.month - 1],
        year=start_date.year,
        current_month=f'{start_date.year}-{start_date.month:02d}',
        cache_info={
            'fetched_at': calendar_data.fetched_at.isoformat(),
            'age_seconds': age_seconds,
            'ttl_seconds': current_app.config.get(
                'CALENDAR_CACHE_TTL_SECONDS',
                300,
            ),
        },
    )


@main.route('/agenda/cache/refresh', methods=['POST'])
@login_required
@require_admin
@limiter.limit('6 per minute')
def refresh_calendar_cache():
    _, _, cache_service = _calendar_context()
    if cache_service is None:
        return jsonify({'ok': False, 'error': 'Agenda não configurada.'}), 400
    calendar_data = cache_service.get_calendar_data(force_refresh=True)
    ok = calendar_data.source_status != 'error'
    return jsonify({
        'ok': ok,
        'message': (
            'Agenda atualizada.'
            if ok
            else 'Não foi possível atualizar a agenda.'
        ),
        'events_count': len(calendar_data.events),
        'fetched_at': calendar_data.fetched_at.isoformat(),
        'source_status': calendar_data.source_status,
        'error': calendar_data.last_error,
    }), 200 if ok else 502


@main.route('/agenda/cache/info', methods=['GET'])
@login_required
@require_admin
def calendar_cache_info():
    _, _, cache_service = _calendar_context()
    if cache_service is None:
        return jsonify({'ok': False, 'error': 'Agenda não configurada.'}), 400
    data = cache_service.get_calendar_data()
    age = (
        datetime.utcnow() - data.fetched_at
    ).total_seconds() if data.fetched_at else None
    ttl = current_app.config.get('CALENDAR_CACHE_TTL_SECONDS', 300)
    return jsonify({
        'ok': True,
        'cache_info': {
            'events_count': len(data.events),
            'fetched_at': data.fetched_at.isoformat() if data.fetched_at else None,
            'age_seconds': age,
            'ttl_seconds': ttl,
            'expired': age is None or age > ttl,
            'source_status': data.source_status,
            'last_error': data.last_error,
        },
    })


def _same_specialty(surgery_request, specialty):
    specialty_id = (
        surgery_request.specialty_id
        or getattr(surgery_request.patient, 'specialty_id', None)
    )
    return specialty_id == specialty.id


def _normalize_match_text(value):
    return ' '.join(str(value or '').casefold().split())


def _resolve_surgery_for_event(event, saved_status, specialty):
    event_date = _event_local_date(event)
    if (
        saved_status
        and saved_status.surgery_request
        and _same_specialty(saved_status.surgery_request, specialty)
    ):
        return saved_status.surgery_request, 'saved-link'

    description = event.get('description') or ''
    marker = _REQUEST_REFERENCE_RE.search(description)
    if marker:
        surgery_request = SurgeryRequest.query.options(
            joinedload(SurgeryRequest.patient)
        ).filter_by(id=int(marker.group(1))).first()
        if (
            surgery_request
            and surgery_request.data_cirurgia == event_date
            and _same_specialty(surgery_request, specialty)
        ):
            return surgery_request, 'reference'

    surgery_request = SurgeryRequest.query.options(
        joinedload(SurgeryRequest.patient)
    ).filter_by(scheduled_event_id=event.get('uid')).first()
    if surgery_request and _same_specialty(surgery_request, specialty):
        return surgery_request, 'event-id'

    candidates = SurgeryRequest.query.options(
        joinedload(SurgeryRequest.patient)
    ).filter(SurgeryRequest.data_cirurgia == event_date).all()
    title = _normalize_match_text(event.get('title'))
    safe_matches = []
    for candidate in candidates:
        if not _same_specialty(candidate, specialty):
            continue
        if _normalize_match_text(candidate.procedimento_solicitado) != title:
            continue
        prontuario = str(getattr(candidate.patient, 'prontuario', '') or '').strip()
        if prontuario and prontuario.casefold() in description.casefold():
            safe_matches.append(candidate)
    if len(safe_matches) == 1:
        return safe_matches[0], 'legacy-unique'
    return None, 'ambiguous' if safe_matches else 'not-found'


def _find_cached_event(cache_service, event_uid, event_date):
    data = cache_service.get_calendar_data()
    matches = [
        event
        for event in data.events
        if event.get('uid') == event_uid
        and _event_local_date(event) == event_date
    ]
    return matches[0] if len(matches) == 1 else None


@main.route('/agenda/events/status', methods=['POST'])
@login_required
@limiter.limit('30 per minute')
def update_event_status():
    from src.models.calendar_event_status import CalendarEventStatus

    data = request.get_json(silent=True) or {}
    event_uid = str(data.get('event_uid', '')).strip()
    status = str(data.get('status', '')).strip().upper()
    reason = str(data.get('reason', '') or '').strip() or None
    if not event_uid or len(event_uid) > 500:
        return jsonify({'ok': False, 'error': 'Evento inválido.'}), 400
    if status not in {'PENDENTE', 'REALIZADA', 'SUSPENSA'}:
        return jsonify({
            'ok': False,
            'error': 'Status deve ser PENDENTE, REALIZADA ou SUSPENSA.',
        }), 400
    if reason and len(reason) > 1000:
        return jsonify({
            'ok': False,
            'error': 'O motivo deve ter no máximo 1000 caracteres.',
        }), 400
    if status != 'SUSPENSA':
        reason = None
    try:
        event_date = datetime.fromisoformat(
            str(data.get('event_date', ''))
        ).date()
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Data do evento inválida.'}), 400

    specialty, _, cache_service = _calendar_context()
    if cache_service is None:
        return jsonify({'ok': False, 'error': 'Agenda não configurada.'}), 400
    event = _find_cached_event(cache_service, event_uid, event_date)
    if event is None:
        return jsonify({
            'ok': False,
            'error': 'O evento não pertence à agenda ativa ou foi atualizado.',
        }), 404

    try:
        saved = CalendarEventStatus.query.filter_by(
            event_uid=event_uid
        ).first()
        surgery_request, link_source = _resolve_surgery_for_event(
            event,
            saved,
            specialty,
        )
        if saved is None:
            saved = CalendarEventStatus(
                event_uid=event_uid,
                event_date=event_date,
                status=status,
            )
            db.session.add(saved)
        saved.event_date = event_date
        saved.status = status
        saved.suspension_reason = reason
        saved.updated_at = datetime.utcnow()

        if surgery_request is not None:
            saved.surgery_request = surgery_request
            surgery_request.scheduled_event_id = event_uid
            surgery_request.status = {
                'PENDENTE': 'Pendente',
                'REALIZADA': 'Realizada',
                'SUSPENSA': 'Suspensa',
            }[status]

        db.session.commit()
        logger.info(
            'Status da agenda atualizado: uid=%s status=%s linked=%s',
            event_uid[:20],
            status,
            bool(surgery_request),
        )
        return jsonify({
            'ok': True,
            'status': status,
            'reason': reason,
            'request_sync': {
                'matched': bool(surgery_request),
                'request_id': surgery_request.id if surgery_request else None,
                'source': link_source,
            },
        })
    except Exception:
        db.session.rollback()
        logger.exception('Erro ao atualizar o status de um evento da agenda.')
        return jsonify({
            'ok': False,
            'error': 'Não foi possível salvar o status do evento.',
        }), 500
