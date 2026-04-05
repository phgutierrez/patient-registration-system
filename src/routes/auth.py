from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user

from src.extensions import db, limiter
from src.forms.user_forms import PasswordChangeForm
from src.models.specialty import Specialty
from src.models.user import User
from src.runtime_security import (
    require_admin,
    generate_temporary_password,
    slugify_username,
)

auth = Blueprint('auth', __name__)


def _get_selected_specialty():
    slug = session.get('specialty_slug')
    if not slug:
        return None
    return Specialty.query.filter_by(slug=slug, is_active=True).first()


def _get_specialty_users(specialty):
    return (
        User.query
        .filter_by(specialty_id=specialty.id)
        .order_by(User.full_name.asc(), User.username.asc())
        .all()
    )


def _build_unique_username(full_name):
    base_username = slugify_username(full_name)
    if not base_username:
        return ''

    candidate = base_username
    suffix = 2
    while User.query.filter_by(username=candidate).first():
        candidate = f'{base_username}{suffix}'
        suffix += 1
    return candidate


@auth.route('/login', methods=['GET'])
def login():
    return redirect(url_for('auth.select_user'))


@auth.route('/', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def select_user():
    """Fluxo de entrada: especialidade -> solicitante -> senha."""
    if current_user.is_authenticated:
        if current_user.must_change_password:
            return redirect(url_for('auth.change_password'))
        return redirect(url_for('main.index'))

    specialty = _get_selected_specialty()
    if not specialty:
        session.pop('pending_user_id', None)
        specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
        return render_template('select_user.html', step='specialty', specialties=specialties)

    users = _get_specialty_users(specialty)
    pending_user = None
    pending_user_id = session.get('pending_user_id')
    if pending_user_id:
        pending_user = User.query.get(pending_user_id)
        if not pending_user or pending_user.specialty_id != specialty.id:
            session.pop('pending_user_id', None)
            pending_user = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'select_user':
            username = (request.form.get('username') or '').strip()
            user = User.query.filter_by(username=username, specialty_id=specialty.id).first()
            if not user:
                flash('Solicitante não encontrado para a especialidade selecionada.', 'error')
            else:
                session['pending_user_id'] = user.id
                session.modified = True
                return redirect(url_for('auth.select_user'))

        elif action == 'authenticate':
            if not pending_user:
                flash('Escolha o solicitante antes de informar a senha.', 'error')
                return redirect(url_for('auth.select_user'))

            password = request.form.get('password') or ''
            if not pending_user.check_password(password):
                flash('Senha inválida. Tente novamente.', 'error')
            else:
                selected_slug = session.get('specialty_slug')
                session.clear()
                if selected_slug:
                    session['specialty_slug'] = selected_slug
                session.permanent = True
                login_user(pending_user, remember=False, fresh=True)

                if pending_user.must_change_password:
                    flash('Antes de continuar, defina uma nova senha.', 'warning')
                    return redirect(url_for('auth.change_password'))

                flash(f'Bem-vindo, {pending_user.full_name}!', 'success')
                return redirect(url_for('main.index'))

        elif action == 'back_to_users':
            session.pop('pending_user_id', None)
            return redirect(url_for('auth.select_user'))

    step = 'password' if pending_user else 'user'
    return render_template(
        'select_user.html',
        step=step,
        users=users,
        specialty=specialty,
        no_users=not users,
        pending_user=pending_user,
    )


@auth.route('/set-specialty', methods=['POST'])
def set_specialty_pre_login():
    """Grava especialidade na sessão antes do login e redireciona para seleção de solicitante."""
    slug = request.form.get('specialty_slug', '').strip()
    sp = Specialty.query.filter_by(slug=slug, is_active=True).first()
    if not sp:
        flash('Especialidade inválida.', 'error')
        return redirect(url_for('auth.select_user'))
    session.clear()
    session['specialty_slug'] = slug
    return redirect(url_for('auth.select_user'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit('10 per hour', methods=['POST'])
def change_password():
    form = PasswordChangeForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('A senha atual informada está incorreta.', 'error')
        else:
            current_user.set_password(form.new_password.data)
            current_user.must_change_password = False
            db.session.commit()
            flash('Senha atualizada com sucesso.', 'success')
            return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('auth.select_user'))


@auth.route('/register_user', methods=['GET', 'POST'])
@login_required
@require_admin
def register_user():
    """Página de gerenciamento de usuários."""
    if request.method == 'POST' and request.form.get('action') == 'add_user':
        full_name = (request.form.get('full_name') or '').strip()
        cns = (request.form.get('cns') or '').strip() or None
        crm = (request.form.get('crm') or '').strip() or None
        role = (request.form.get('role') or 'solicitante').strip().lower()
        specialty_id = request.form.get('specialty_id') or None
        specialty_id = int(specialty_id) if specialty_id else None

        username = _build_unique_username(full_name)
        if not full_name or not username:
            flash('Informe um nome completo válido para criar o solicitante.', 'error')
        else:
            try:
                temporary_password = generate_temporary_password(12)
                user = User(
                    username=username,
                    password=temporary_password,
                    full_name=full_name,
                    cns=cns,
                    crm=crm,
                    role='admin' if role == 'admin' else 'solicitante',
                    specialty_id=specialty_id,
                    must_change_password=True,
                )
                db.session.add(user)
                db.session.commit()
                flash(
                    f'Usuário {full_name} criado com sucesso. Usuário: {username} | senha temporária: {temporary_password}',
                    'success',
                )
                return redirect(url_for('auth.register_user'))
            except Exception as e:
                db.session.rollback()
                flash('Erro ao criar usuário. Verifique se CNS/CRM/usuário já existem.', 'error')

    if request.method == 'POST' and request.form.get('action') == 'edit_user':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)

        if user:
            try:
                user.full_name = (request.form.get('full_name') or '').strip()
                user.cns = (request.form.get('cns') or '').strip() or None
                user.crm = (request.form.get('crm') or '').strip() or None
                sid = request.form.get('specialty_id') or None
                user.specialty_id = int(sid) if sid else None
                role = (request.form.get('role') or user.role).strip().lower()
                user.role = 'admin' if role == 'admin' else 'solicitante'
                db.session.commit()
                flash(f'Usuário {user.full_name} atualizado com sucesso!', 'success')
            except Exception:
                db.session.rollback()
                flash('Erro ao atualizar usuário.', 'error')
        else:
            flash('Usuário não encontrado', 'error')

        return redirect(url_for('auth.register_user'))

    if request.method == 'POST' and request.form.get('action') == 'reset_password':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if not user:
            flash('Usuário não encontrado.', 'error')
        else:
            new_password = generate_temporary_password(12)
            user.set_password(new_password)
            user.must_change_password = True
            db.session.commit()
            flash(
                f'Senha temporária redefinida para {user.full_name}: {new_password}',
                'warning',
            )
        return redirect(url_for('auth.register_user'))

    if request.method == 'POST' and request.form.get('action') == 'delete_user':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)

        if user:
            if user.id == current_user.id:
                flash('Você não pode remover o próprio usuário autenticado.', 'error')
            else:
                try:
                    full_name = user.full_name
                    db.session.delete(user)
                    db.session.commit()
                    flash(f'Usuário {full_name} deletado com sucesso!', 'success')
                except Exception:
                    db.session.rollback()
                    flash('Erro ao deletar usuário.', 'error')
        else:
            flash('Usuário não encontrado', 'error')

        return redirect(url_for('auth.register_user'))

    users = User.query.order_by(User.role.desc(), User.full_name.asc()).all()
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.id).all()
    return render_template('user_registration.html', users=users, specialties=specialties)
