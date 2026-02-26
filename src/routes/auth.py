from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from src.models.user import User
from src.models.specialty import Specialty
from src.extensions import db
from src.forms.user_forms import UserRegistrationForm

auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET', 'POST'])
def select_user():
    """Fluxo de entrada: 1ª seleciona especialidade, 2ª seleciona solicitante filtrado."""
    from flask import session

    # ── Etapa 1: especialidade ainda não escolhida ──────────────────────────
    if not session.get('specialty_slug'):
        specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.name).all()
        return render_template('select_user.html', step='specialty', specialties=specialties)

    # ── Etapa 2: mostrar solicitantes da especialidade ────────────────────
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            login_user(user)
            flash(f'Bem-vindo, {user.full_name}!', 'success')
            return redirect(url_for('main.index'))
        flash('Usuário não encontrado', 'error')

    specialty = Specialty.query.filter_by(slug=session['specialty_slug'], is_active=True).first()
    if specialty and specialty.users:
        users = specialty.users
        no_users = False
    else:
        users = []
        no_users = True

    return render_template('select_user.html', step='user', users=users,
                           specialty=specialty, no_users=no_users)


@auth.route('/set-specialty', methods=['POST'])
def set_specialty_pre_login():
    """Grava especialidade na sessão antes do login e redireciona para seleção de solicitante."""
    from flask import session
    slug = request.form.get('specialty_slug', '').strip()
    sp = Specialty.query.filter_by(slug=slug, is_active=True).first()
    if not sp:
        flash('Especialidade inválida.', 'error')
        return redirect(url_for('auth.select_user'))
    session['specialty_slug'] = slug
    return redirect(url_for('auth.select_user'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('auth.select_user'))


@auth.route('/register_user', methods=['GET', 'POST'])
def register_user():
    """Página de gerenciamento de usuários"""
    
    # Formulário para adicionar novo usuário
    if request.method == 'POST' and request.form.get('action') == 'add_user':
        full_name = request.form.get('full_name')
        cns = request.form.get('cns')
        crm = request.form.get('crm')
        
        # Extrai o primeiro nome para usar como username
        username = full_name.split()[0].lower() if full_name else ''
        
        specialty_id = request.form.get('specialty_id') or None
        if specialty_id:
            specialty_id = int(specialty_id)
        # pre-fill from session if form didn't send
        if not specialty_id:
            from flask import session as _s
            slug = _s.get('specialty_slug')
            if slug:
                _sp = Specialty.query.filter_by(slug=slug).first()
                if _sp:
                    specialty_id = _sp.id

        # Verifica se o usuário já existe
        if User.query.filter_by(username=username).first():
            flash(f'Usuário {username} já existe', 'error')
        else:
            try:
                user = User(
                    username=username,
                    password='123456',  # Senha padrão
                    full_name=full_name,
                    cns=cns if cns else None,
                    crm=crm if crm else None,
                    role='solicitante',
                    specialty_id=specialty_id,
                )
                db.session.add(user)
                db.session.commit()
                flash(f'Usuário {full_name} criado com sucesso!', 'success')
                # redirecionar de volta ao login para que o novo usuário já apareça
                return redirect(url_for('auth.select_user'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar usuário: {str(e)}', 'error')
    
    # Editar usuário
    if request.method == 'POST' and request.form.get('action') == 'edit_user':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        
        if user:
            try:
                user.full_name = request.form.get('full_name')
                user.cns = request.form.get('cns') or None
                user.crm = request.form.get('crm') or None
                sid = request.form.get('specialty_id') or None
                user.specialty_id = int(sid) if sid else None
                db.session.commit()
                flash(f'Usuário {user.full_name} atualizado com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
        else:
            flash('Usuário não encontrado', 'error')
        
        return redirect(url_for('auth.register_user'))
    
    # Deletar usuário
    if request.method == 'POST' and request.form.get('action') == 'delete_user':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        
        if user:
            try:
                full_name = user.full_name
                db.session.delete(user)
                db.session.commit()
                flash(f'Usuário {full_name} deletado com sucesso!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao deletar usuário: {str(e)}', 'error')
        else:
            flash('Usuário não encontrado', 'error')
        
        return redirect(url_for('auth.register_user'))
    
    # Listar todos os usuários
    users = User.query.all()
    specialties = Specialty.query.filter_by(is_active=True).order_by(Specialty.id).all()

    return render_template('user_registration.html', users=users, specialties=specialties)
