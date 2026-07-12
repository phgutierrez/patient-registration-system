# src/routes/specialty_settings.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from src.extensions import db
from src.models.specialty import Specialty, SpecialtySettings, SpecialtyProcedure
from src.runtime_security import require_admin
from src.services.access_patient_service import (
    AccessConfig, AccessLookupError, access_patient_service, validate_access_config,
)

specialty_settings_bp = Blueprint('specialty_settings', __name__, url_prefix='/configuracoes')


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

    access_config = AccessConfig(
        host=request.form.get('access_host', '').strip(),
        share_path=request.form.get('access_share_path', '').strip(),
        filename=request.form.get('access_filename', '').strip(),
        enabled=request.form.get('access_enabled') == 'on',
    )
    try:
        validate_access_config(access_config)
    except ValueError as exc:
        flash(f'Configuração do Access inválida: {exc}', 'error')
        return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')

    settings.agenda_url = request.form.get('agenda_url', '').strip() or None
    settings.forms_url = request.form.get('forms_url', '').strip() or None
    settings.access_host = access_config.host
    settings.access_share_path = access_config.share_path.strip('\\')
    settings.access_filename = access_config.filename
    settings.access_enabled = access_config.enabled

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
    Specialty.query.filter_by(id=specialty_id, slug='ortopedia').first_or_404()
    config = AccessConfig(
        host=request.form.get('access_host', '').strip(),
        share_path=request.form.get('access_share_path', '').strip(),
        filename=request.form.get('access_filename', '').strip(),
        enabled=True,
    )
    try:
        validate_access_config(config)
        result = access_patient_service.test_connection(config)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({'ok': False, 'code': 'ACCESS_CONFIG_INVALID', 'message': str(exc), 'hint': 'Revise os três campos de conexão.'}), 400
    except AccessLookupError as exc:
        return jsonify(exc.payload()), exc.status


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
    sort_order = request.form.get('sort_order', 0)

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
        proc = SpecialtyProcedure(
            specialty_id=specialty_id,
            descricao=descricao,
            codigo_sus=codigo_sus or None,
            sort_order=int(sort_order) if sort_order else 0,
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
    proc.sort_order = int(request.form.get('sort_order', proc.sort_order) or 0)

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
