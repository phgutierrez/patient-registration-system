"""Controle de cirurgias (somente leitura, somente administradores).

Lê Ocorrencias_SS no Access em **segundo plano** (``access_surgery_service``).
As rotas nunca esperam o Access: respondem com o último snapshot ou com um painel
de carregamento que se atualiza sozinho. Nada é gravado.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for
from flask_login import login_required

from src.extensions import limiter
from src.htmx_utils import is_htmx_partial_request, render_page_or_partial
from src.routes.today import _access_config
from src.runtime_security import require_admin
from src.services.access_surgery_service import (
    STATUS_CANCELED, STATUS_DONE, STATUS_LABELS, STATUS_NO_ANSWER, STATUS_UNKNOWN,
    access_surgery_service, build_calendar, count_by_status, filter_list, period_bounds,
    rows_in_period, shift_anchor, suspension_summary,
)

logger = logging.getLogger(__name__)
surgery_control_bp = Blueprint('surgery_control', __name__, url_prefix='/controle-cirurgias')

VIEWS = ('month', 'week')
STATUS_FILTERS = (STATUS_NO_ANSWER, STATUS_CANCELED, STATUS_DONE, STATUS_UNKNOWN)
LIST_LIMIT = 300
POLL_SECONDS = 2
MONTHS = ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
          'setembro', 'outubro', 'novembro', 'dezembro')
WEEKDAYS = ('Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo')


def _parse_iso(value, default: date) -> date:
    try:
        return datetime.strptime((value or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return default


def _period_title(view: str, start: date, end: date) -> str:
    if view == 'week':
        return f'{start.strftime("%d/%m/%Y")} a {end.strftime("%d/%m/%Y")}'
    return f'{MONTHS[start.month - 1].capitalize()} de {start.year}'


def _prepare_service():
    """Define a pasta da cópia local (instance/access_cache) e devolve a config do Access."""
    base = current_app.config.get('INSTANCE_PATH') or current_app.instance_path
    access_surgery_service.configure(Path(base) / 'access_cache')
    return _access_config()


def _params(source) -> dict:
    today = date.today()
    view = source.get('view') if source.get('view') in VIEWS else 'month'
    status = source.get('status') if source.get('status') in STATUS_FILTERS else ''
    return {
        'view': view,
        'anchor': _parse_iso(source.get('date'), today),
        'status': status,
        'query': (source.get('q') or '').strip()[:80],
        'only_undated': source.get('sem_data') == '1',
        'today': today,
    }


def _render_index(params: dict, config):
    today, view, anchor = params['today'], params['view'], params['anchor']
    start, end = period_bounds(view, anchor)
    state = access_surgery_service.get_view(config, today)
    snapshot = state.snapshot
    if snapshot is not None and not params['only_undated'] and not access_surgery_service.is_covered(start):
        state = access_surgery_service.ensure_range(config, start)
        snapshot = state.snapshot
    period_pending = (snapshot is not None and not params['only_undated']
                      and not access_surgery_service.is_covered(start))
    waiting = (snapshot is None and state.status == 'loading') or period_pending
    context = {
        'view': view, 'anchor': anchor, 'today': today, 'status_filter': params['status'],
        'query': params['query'], 'only_undated': params['only_undated'], 'start': start, 'end': end,
        'title_period': _period_title(view, start, end),
        'prev_date': shift_anchor(view, anchor, -1), 'next_date': shift_anchor(view, anchor, 1),
        'status_labels': STATUS_LABELS, 'weekdays': WEEKDAYS,
        'load_state': 'loading' if waiting else ('error' if snapshot is None else 'ready'),
        'polling': state.status == 'loading', 'poll_seconds': POLL_SECONDS,
        'refreshing': snapshot is not None and state.status == 'loading' and not period_pending,
        'phase': state.phase, 'elapsed': int(state.elapsed), 'reason': state.reason,
        'period_pending': period_pending, 'error': state.error if snapshot is None else None,
        'refresh_error': state.error if snapshot is not None else None,
        'age_minutes': None if state.age is None else int(state.age // 60),
        'warnings': (), 'synced_at': None, 'origin': '', 'calendar': None, 'counts': None,
        'list_rows': [], 'list_total': 0, 'undated_total': 0, 'undated_since': None, 'suspensions': None,
        'self_url': url_for('surgery_control.index', view=view, date=anchor.isoformat(),
                            status=params['status'] or None, q=params['query'] or None,
                            sem_data='1' if params['only_undated'] else None),
    }
    if snapshot is not None and not waiting:
        period_rows = rows_in_period(snapshot.rows, start, end)
        undated = [row for row in snapshot.rows if row.programada is None]
        listed = filter_list(undated if params['only_undated'] else period_rows,
                             params['status'], params['query'])
        context.update(
            warnings=snapshot.warnings, synced_at=snapshot.synced_at, origin=snapshot.origin,
            calendar=build_calendar(view, anchor, snapshot.rows, today),
            counts=count_by_status(period_rows),
            list_rows=listed[:LIST_LIMIT], list_total=len(listed),
            undated_total=len(undated), undated_since=snapshot.undated_since,
            suspensions=suspension_summary(period_rows),
        )
    return render_page_or_partial('surgery_control/index.html', 'surgery_control/_app.html', **context)


@surgery_control_bp.route('/', methods=['GET'])
@login_required
@require_admin
@limiter.limit('120 per minute')
def index():
    return _render_index(_params(request.args), _prepare_service())


@surgery_control_bp.route('/atualizar', methods=['POST'])
@login_required
@require_admin
@limiter.limit('10 per minute')
def refresh():
    """Pede nova leitura do Access (em segundo plano) e volta à tela."""
    params = _params(request.form)
    config = _prepare_service()
    access_surgery_service.refresh(config, params['today'])
    if is_htmx_partial_request():
        return _render_index(params, config)
    return redirect(url_for('surgery_control.index', view=params['view'], date=params['anchor'].isoformat()), code=303)


@surgery_control_bp.route('/dia/<day>', methods=['GET'])
@login_required
@require_admin
@limiter.limit('240 per minute')
def day_detail(day: str):
    try:
        selected = datetime.strptime(day, '%Y-%m-%d').date()
    except ValueError:
        abort(404)
    view = request.args.get('view') if request.args.get('view') in VIEWS else 'month'
    state = access_surgery_service.get_view(_prepare_service())  # só memória: nunca espera o Access
    rows, notice = [], ''
    if state.snapshot is None:
        notice = 'Os dados ainda estão sendo carregados. Tente novamente em instantes.'
    elif not access_surgery_service.is_covered(selected):
        notice = 'Este período ainda não foi carregado. Navegue até ele no calendário para carregá-lo.'
    else:
        rows = rows_in_period(state.snapshot.rows, selected, selected)
    return render_template('surgery_control/_day.html', day=selected, rows=rows, error=None,
                           notice=notice, weekdays=WEEKDAYS, view=view)
