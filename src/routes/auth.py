from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from src.models.user import User
from src.extensions import db
from src.forms.user_forms import UserRegistrationForm

auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET', 'POST'])
def select_user():
    """Página inicial com seleção de usuário"""
    if request.method == 'POST':
        username = request.form.get('username')
        
        user = User.query.filter_by(username=username).first()
        if user:
            login_user(user)
            flash(f'Bem-vindo, {user.full_name}!', 'success')
            return redirect(url_for('main.index'))
        
        flash('Usuário não encontrado', 'error')
    
    users = User.query.all()
    return render_template('select_user.html', users=users)


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
                    role='solicitante'
                )
                db.session.add(user)
                db.session.commit()
                flash(f'Usuário {full_name} criado com sucesso!', 'success')
                return redirect(url_for('auth.register_user'))
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
    
    return render_template('user_registration.html', users=users)
