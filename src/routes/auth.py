from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from src.models.user import User
from src.extensions import db
from src.forms.user_forms import UserRegistrationForm

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Login bem-sucedido!', 'success')
            return redirect(next_page or url_for('main.index'))

        flash('Usuário ou senha inválidos', 'error')
    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/register_user', methods=['GET', 'POST'])
@login_required
def register_user():
    """Rota para o usuário logado preencher/atualizar seus dados."""
    form = UserRegistrationForm(obj=current_user)

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.cns = form.cns.data if form.cns.data else None
        current_user.crm = form.crm.data if form.crm.data else None

        try:
            db.session.commit()
            flash('Informações atualizadas com sucesso!', 'success')
            return redirect(url_for('auth.register_user'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar informações: {e}', 'error')

    return render_template('user_registration.html', form=form)
