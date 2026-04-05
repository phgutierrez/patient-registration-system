# src/routes/specialty_settings.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from src.extensions import db
from src.models.specialty import Specialty, SpecialtySettings, SpecialtyProcedure
from src.runtime_security import require_admin

specialty_settings_bp = Blueprint('specialty_settings', __name__, url_prefix='/configuracoes')


# ---------------------------------------------------------------------------
# Index – lista especialidades e permite editar configurações
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/', methods=['GET'])
@login_required
@require_admin
def index():
    specialties = Specialty.query.order_by(Specialty.id).all()
    return render_template('specialty_settings/index.html', specialties=specialties)


# ---------------------------------------------------------------------------
# Salvar configurações (agenda_url + forms_url) de uma especialidade
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/especialidade/<int:specialty_id>/settings', methods=['POST'])
@login_required
@require_admin
def save_settings(specialty_id):
    specialty = Specialty.query.get_or_404(specialty_id)
    settings = specialty.settings
    if settings is None:
        settings = SpecialtySettings(specialty_id=specialty_id)
        db.session.add(settings)

    settings.agenda_url = request.form.get('agenda_url', '').strip() or None
    settings.forms_url = request.form.get('forms_url', '').strip() or None

    try:
        db.session.commit()
        flash(f'Configurações de {specialty.name} salvas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar: {str(e)}', 'error')

    return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')


# ---------------------------------------------------------------------------
# Adicionar procedimento
# ---------------------------------------------------------------------------
@specialty_settings_bp.route('/especialidade/<int:specialty_id>/procedimentos/add', methods=['POST'])
@login_required
@require_admin
def add_procedure(specialty_id):
    specialty = Specialty.query.get_or_404(specialty_id)
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
    proc = SpecialtyProcedure.query.get_or_404(proc_id)
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
    proc = SpecialtyProcedure.query.get_or_404(proc_id)
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
    proc = SpecialtyProcedure.query.get_or_404(proc_id)
    specialty_id = proc.specialty_id
    try:
        db.session.delete(proc)
        db.session.commit()
        flash(f'Procedimento "{proc.descricao}" removido.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro: {str(e)}', 'error')

    return redirect(url_for('specialty_settings.index') + f'#esp-{specialty_id}')
