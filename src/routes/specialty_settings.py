# src/routes/specialty_settings.py
import threading

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from src.extensions import db, limiter
from src.models.specialty import Specialty, SpecialtySettings, SpecialtyProcedure
from src.runtime_security import require_admin, request_is_loopback
from src.services.access_patient_service import (
    AccessConfig, AccessLookupError, access_patient_service, validate_access_config,
)
from src.services.windows_file_picker import (
    FilePickerError, pick_local_access_database, validate_local_access_path,
)

specialty_settings_bp = Blueprint('specialty_settings', __name__, url_prefix='/configuracoes')
_procedure_order_lock = threading.Lock()


def _access_config_from_form(settings, *, enabled=None):
    source = (request.form.get('access_source') or getattr(settings, 'access_source', None) or 'network').strip().lower()
    return AccessConfig(
        host=(request.form.get('access_host') or getattr(settings, 'access_host', None) or '192.168.1.252').strip(),
        share_path=(request.form.get('access_share_path') or getattr(settings, 'access_share_path', None) or r'naqh\AMBULATORIO_SERV').strip(),
        filename=(request.form.get('access_filename') or getattr(settings, 'access_filename', None) or 'AMBULATORIO_SERV.accdb').strip(),
        enabled=(request.form.get('access_enabled') == 'on') if enabled is None else enabled,
        source=source,
        local_path=(request.form.get('access_local_path') or getattr(settings, 'access_local_path', None) or '').strip() or None,
    )


# ---------------------------------------------------------------------------
# Index – lista especialidades e permite editar configurações
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/', methods=['GET'])
@login_required
@require_admin
def index():
    specialties = Specialty.query.filter_by(slug='ortopedia').all()
    return render_template('specialty_settings/index.html', specialties=specialties)


# ---------------------------------------------------------------------------
# Salvar configurações (agenda_url + forms_url) de uma especialidade
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/especialidade/<int:specialty_id>/settings', methods=['POST'])
@login_required
@require_admin
def save_settings(specialty_id):
    specialty = Specialty.query.filter_by(id=specialty_id, slug='ortopedia').first_or_404()
    settings = specialty.settings
    if settings is None:
        settings = SpecialtySettings(specialty_id=specialty_id)
        db.session.add(settings)

    access_config = _access_config_from_form(settings)
    try:
        validate_access_config(access_config)
        if access_config.source == 'local':
            validate_local_access_path(access_config.local_path or '')
    except ValueError as exc:
        flash(f'Configuração do Access inválida: {exc}', 'error')
        return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')

    settings.agenda_url = request.form.get('agenda_url', '').strip() or None
    settings.forms_url = request.form.get('forms_url', '').strip() or None
    settings.access_host = access_config.host
    settings.access_share_path = access_config.share_path.strip('\\')
    settings.access_filename = access_config.filename
    settings.access_enabled = access_config.enabled
    settings.access_source = access_config.source
    settings.access_local_path = access_config.local_path

    try:
        db.session.commit()
        access_patient_service.invalidate()
        flash(f'Configurações de {specialty.name} salvas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar: {str(e)}', 'error')

    return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')


@specialty_settings_bp.route('/especialidade/<int:specialty_id>/access/test', methods=['POST'])
@login_required
@require_admin
def test_access_connection(specialty_id):
    specialty = Specialty.query.filter_by(id=specialty_id, slug='ortopedia').first_or_404()
    config = _access_config_from_form(specialty.settings, enabled=True)
    try:
        validate_access_config(config)
        result = access_patient_service.test_connection(config)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({'ok': False, 'code': 'ACCESS_CONFIG_INVALID', 'message': str(exc), 'hint': 'Revise a origem e os campos de conexão.'}), 400
    except AccessLookupError as exc:
        return jsonify(exc.payload()), exc.status


@specialty_settings_bp.route('/access/select-local-file', methods=['POST'])
@login_required
@require_admin
@limiter.limit('5 per minute')
def select_local_access_file():
    if not request_is_loopback():
        return jsonify({
            'ok': False,
            'code': 'LOCAL_PICKER_REQUIRES_SERVER',
            'message': 'A janela de arquivos só pode ser aberta no próprio computador servidor.',
            'hint': 'Abra Configurações usando localhost no computador onde o sistema está executando.',
        }), 403
    payload = request.get_json(silent=True) or {}
    try:
        selected = pick_local_access_database(payload.get('initial_path'))
    except FilePickerError as exc:
        return jsonify({'ok': False, 'code': 'LOCAL_PICKER_FAILED', 'message': str(exc), 'hint': 'Informe o caminho manualmente ou tente novamente.'}), 503
    if selected is None:
        return jsonify({'ok': True, 'selected': False, 'message': 'Seleção cancelada.'}), 200
    return jsonify({
        'ok': True,
        'selected': True,
        'path': selected,
        'filename': selected.replace('/', '\\').rsplit('\\', 1)[-1],
        'message': 'Arquivo local selecionado.',
    }), 200


# ---------------------------------------------------------------------------
# Adicionar procedimento
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/especialidade/<int:specialty_id>/procedimentos/add', methods=['POST'])
@login_required
@require_admin
def add_procedure(specialty_id):
    specialty = Specialty.query.filter_by(id=specialty_id, slug='ortopedia').first_or_404()
    descricao = request.form.get('descricao', '').strip()
    codigo_sus = request.form.get('codigo_sus', '').strip()

    if not descricao:
        flash('Descrição é obrigatória.', 'error')
        return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')

    existing = SpecialtyProcedure.query.filter_by(
        specialty_id=specialty_id, descricao=descricao
    ).first()
    if existing:
        flash(f'Procedimento "{descricao}" já existe nessa especialidade.', 'warning')
        return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')

    try:
        # O executável usa um único processo Waitress. O lock mantém max + insert
        # atômicos entre suas threads e evita posições repetidas em cliques simultâneos.
        with _procedure_order_lock:
            greatest_order = (
                db.session.query(db.func.max(SpecialtyProcedure.sort_order))
                .filter(SpecialtyProcedure.specialty_id == specialty_id)
                .scalar()
            )
            proc = SpecialtyProcedure(
                specialty_id=specialty_id,
                descricao=descricao,
                codigo_sus=codigo_sus or None,
                sort_order=(greatest_order + 1) if greatest_order is not None else 0,
            )
            db.session.add(proc)
            db.session.commit()
        flash(f'Procedimento "{descricao}" adicionado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')

    return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')


# ---------------------------------------------------------------------------
# Editar procedimento
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/procedimentos/<int:proc_id>/edit', methods=['POST'])
@login_required
@require_admin
def edit_procedure(proc_id):
    proc = (SpecialtyProcedure.query.join(Specialty)
            .filter(SpecialtyProcedure.id == proc_id, Specialty.slug == 'ortopedia')
            .first_or_404())
    proc.descricao = request.form.get('descricao', proc.descricao).strip()
    proc.codigo_sus = request.form.get('codigo_sus', '').strip() or None

    try:
        db.session.commit()
        flash('Procedimento atualizado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')

    return redirect(url_for('specialty_settings.index') + f'#esp-{proc.specialty_id}')


# ---------------------------------------------------------------------------
# Ativar / desativar procedimento
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/procedimentos/<int:proc_id>/toggle', methods=['POST'])
@login_required
@require_admin
def toggle_procedure(proc_id):
    proc = (SpecialtyProcedure.query.join(Specialty)
            .filter(SpecialtyProcedure.id == proc_id, Specialty.slug == 'ortopedia')
            .first_or_404())
    proc.is_active = not proc.is_active
    try:
        db.session.commit()
        status = 'ativado' if proc.is_active else 'desativado'
        flash(f'Procedimento "{proc.descricao}" {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')

    return redirect(url_for('specialty_settings.index') + f'#esp-{proc.specialty_id}')


# ---------------------------------------------------------------------------
# Remover procedimento
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/procedimentos/<int:proc_id>/delete', methods=['POST'])
@login_required
@require_admin
def delete_procedure(proc_id):
    proc = (SpecialtyProcedure.query.join(Specialty)
            .filter(SpecialtyProcedure.id == proc_id, Specialty.slug == 'ortopedia')
            .first_or_404())
    specialty_id = proc.specialty_id
    try:
        db.session.delete(proc)
        db.session.commit()
        flash(f'Procedimento "{proc.descricao}" removido.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')

    return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')
