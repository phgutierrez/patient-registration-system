"""Autogestão segura dos dados do usuário autenticado."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from src.extensions import db, limiter
from src.models.user import User
from src.password_policy import is_valid_pin


profile_bp = Blueprint('profile', __name__)


def _normalized_cns(value: str) -> str | None:
    normalized = (value or '').strip()
    if not normalized:
        return None
    if not normalized.isdigit() or len(normalized) != 15:
        raise ValueError('O CNS deve conter exatamente 15 dígitos.')
    return normalized


def _normalized_crm(value: str) -> str | None:
    normalized = ' '.join((value or '').strip().upper().split())
    if not normalized:
        return None
    if len(normalized) > 20:
        raise ValueError('O CRM deve conter no máximo 20 caracteres.')
    return normalized


@profile_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
@limiter.limit('20 per hour', methods=['POST'])
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        current_pin = request.form.get('current_pin') or ''
        if not current_user.check_password(current_pin):
            flash('O PIN atual está incorreto.', 'error')
            return render_template('auth/profile.html'), 400

        if action == 'update_profile':
            try:
                full_name = ' '.join(
                    (request.form.get('full_name') or '').strip().split()
                )
                if not 3 <= len(full_name) <= 100:
                    raise ValueError('Informe um nome completo válido.')
                cns = _normalized_cns(request.form.get('cns') or '')
                crm = _normalized_crm(request.form.get('crm') or '')
                cns_owner = (
                    User.query.filter(User.cns == cns, User.id != current_user.id).first()
                    if cns else None
                )
                crm_owner = (
                    User.query.filter(User.crm == crm, User.id != current_user.id).first()
                    if crm else None
                )
                if cns_owner:
                    raise ValueError('Este CNS já pertence a outro usuário.')
                if crm_owner:
                    raise ValueError('Este CRM já pertence a outro usuário.')
                current_user.full_name = full_name
                current_user.cns = cns
                current_user.crm = crm
                db.session.commit()
                flash('Seus dados foram atualizados.', 'success')
                return redirect(url_for('profile.profile'))
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), 'error')
            except Exception:
                db.session.rollback()
                flash('Não foi possível atualizar seus dados.', 'error')

        elif action == 'change_pin':
            new_pin = request.form.get('new_pin') or ''
            confirmation = request.form.get('confirm_pin') or ''
            if not is_valid_pin(new_pin):
                flash('O novo PIN deve conter exatamente 6 dígitos.', 'error')
            elif new_pin != confirmation:
                flash('A confirmação do novo PIN não coincide.', 'error')
            else:
                current_user.set_password(new_pin)
                current_user.must_change_password = False
                db.session.commit()
                flash('Seu PIN foi alterado.', 'success')
                return redirect(url_for('profile.profile'))
        else:
            flash('Ação de perfil inválida.', 'error')

    return render_template('auth/profile.html')
