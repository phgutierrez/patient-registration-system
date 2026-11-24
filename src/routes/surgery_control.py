"""Controle de cirurgias (somente leitura, somente administradores).

Lê Ocorrencias_SS no Access via ``access_surgery_service``. Nada é gravado.
"""
from __future__ import annotations

import logging
from datetime import date, datetime

from flask import Blueprint, abort, render_template, request
from flask_login import login_required

from src.extensions import limiter
from src.htmx_utils import render_page_or_partial
from src.routes.today import _access_config
from src.runtime_security import require_admin
from src.services.access_patient_service import AccessLookupError
from src.services.access_surgery_service import (
    SNAPSHOT_TTL, STATUS_DONE, STATUS_LABELS, STATUS_NO_ANSWER, STATUS_CANCELED, STATUS_UNKNOWN,
    access_surgery_service, build_calendar, count_by_status, filter_list, period_bounds,
    rows_in_period, shift_anchor, suspension_summary,
)

logger = logging.getLogger(__name__)
surgery_control_bp = Blueprint('surgery_control', __name__, url_prefix='/controle-cirurgias')

VIEWS = ('month', 'week')
STATUS_FILTERS = (STATUS_NO_ANSWER, STATUS_CANCELED, STATUS_DONE, STATUS_UNKNOWN)
UNDATED_LIST_LIMIT = 200
MONTHS = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
          'setembro', 'outubro', 'novembro', 'dezembro')
WEEKDAYS = ('Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo')


def _parse_iso(value, default: date) -> date:
    try:
        return datetime.strptime((value or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return default


def _error_context(exc: Exception) -> dict:
    if isinstance(exc, AccessLookupError):
        logger.warning('Controle de cirurgias indisponível: %s', exc.code)
        return {'message': exc.message, 'hint': exc.hint}
    logger.warning('Configuração Access inválida para o controle de cirurgias.')
    return {'message': 'A configuração do banco Access é inválida.',
            'hint': 'Revise o banco Access nas Configurações.'}


def _period_title(view: str, start: date, end: date) -> str:
    if view == 'week':
        return f'{start.strftime("%d/%m/%Y")} a {end.strftime("%d/%m/%Y")}'
    return f'{MONTHS[start.month - 1].capitalize()} de {start.year}'


@surgery_control_bp.route('/', methods=['GET'])
@login_required
@require_admin
@limiter.limit('60 per minute')
def index():
    today = date.today()
    view = request.args.get('view') if request.args.get('view') in VIEWS else 'month'
    anchor = _parse_iso(request.args.get('date'), today)
    status = request.args.get('status') if request.args.get('status') in STATUS_FILTERS else ''
    query = (request.args.get('q') or '').strip()[:80]
    only_undated = request.args.get('sem_data') == '1'
    start, end = period_bounds(view, anchor)
    context = {
        'view': view, 'anchor': anchor, 'today': today, 'status_filter': status, 'query': query,
        'only_undated': only_undated, 'start': start, 'end': end,
        'title_period': _period_title(view, start, end),
        'prev_date': shift_anchor(view, anchor, -1), 'next_date': shift_anchor(view, anchor, 1),
        'error': None, 'warnings': (), 'synced_at': None, 'calendar': None, 'counts': None,
        'list_rows': [], 'undated_total': 0, 'undated_truncated': False, 'suspensions': None,
        'status_labels': STATUS_LABELS, 'weekdays': WEEKDAYS, 'refresh_seconds': SNAPSHOT_TTL,
    }
    try:
        snapshot = access_surgery_service.load(_access_config(), force=request.args.get('sync') == '1')
    except (ValueError, AccessLookupError) as exc:
        context['error'] = _error_context(exc)
        return render_page_or_partial('surgery_control/index.html', 'surgery_control/_app.html', **context)

    period_rows = rows_in_period(snapshot.rows, start, end)
    undated = [row for row in snapshot.rows if row.programada is None]
    source_rows = undated if only_undated else period_rows
    list_rows = filter_list(source_rows, status, query)
    context.update(
        warnings=snapshot.warnings, synced_at=snapshot.synced_at,
        calendar=build_calendar(view, anchor, snapshot.rows, today),
        counts=count_by_status(period_rows),
        list_rows=list_rows[:UNDATED_LIST_LIMIT] if only_undated else list_rows,
        undated_total=len(undated),
        undated_truncated=only_undated and len(list_rows) > UNDATED_LIST_LIMIT,
        suspensions=suspension_summary(period_rows),
    )
    return render_page_or_partial('surgery_control/index.html', 'surgery_control/_app.html', **context)


@surgery_control_bp.route('/dia/<day>', methods=['GET'])
@login_required
@require_admin
@limiter.limit('120 per minute')
def day_detail(day: str):
    try:
        selected = datetime.strptime(day, '%Y-%m-%d').date()
    except ValueError:
        abort(404)
    view = request.args.get('view') if request.args.get('view') in VIEWS else 'month'
    error, rows = None, []
    try:
        snapshot = access_surgery_service.load(_access_config())
        rows = rows_in_period(snapshot.rows, selected, selected)
    except (ValueError, AccessLookupError) as exc:
        error = _error_context(exc)
    return render_template('surgery_control/_day.html', day=selected, rows=rows, error=error,
                           weekdays=WEEKDAYS, view=view)
