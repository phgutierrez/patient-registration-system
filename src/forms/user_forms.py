from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional, Length, Regexp, EqualTo

PIN_VALIDATOR = Regexp(r'^\d{6}$', message='A senha deve conter exatamente 6 dígitos.')


class UserRegistrationForm(FlaskForm):
    """Formulário para cadastro/atualização de dados do usuário."""
    full_name = StringField(
        'Nome Completo',
        validators=[DataRequired(
            "Nome completo é obrigatório."), Length(min=3, max=100)]
    )
    cns = StringField(
        'CNS',
        validators=[
            Optional(),
            Length(min=15, max=15, message="CNS deve ter 15 dígitos."),
            Regexp(r'^[0-9]*$', message="CNS deve conter apenas números.")
        ]
    )
    crm = StringField(
        'CRM',
        validators=[
            Optional(),
            # Ajuste o tamanho conforme necessário
            Length(min=5, max=20, message="CRM inválido.")
            # Pode adicionar regex para formato específico de CRM se necessário
        ]
    )
    submit = SubmitField('Salvar Informações')


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField(
        'Senha Atual',
        validators=[DataRequired("Informe sua senha atual.")]
    )
    new_password = PasswordField(
        'Nova Senha',
        validators=[DataRequired("Informe a nova senha."), PIN_VALIDATOR]
    )
    confirm_password = PasswordField(
        'Confirmar Nova Senha',
        validators=[
            DataRequired("Confirme a nova senha."),
            EqualTo('new_password', message='As senhas não coincidem.')
        ]
    )
    submit = SubmitField('Alterar Senha')


class FirstAdminForm(FlaskForm):
    full_name = StringField(
        'Nome completo',
        validators=[DataRequired('Informe o nome completo.'), Length(min=3, max=100)],
    )
    username = StringField(
        'Usuário',
        validators=[
            DataRequired('Informe o usuário.'),
            Length(min=3, max=80),
            Regexp(r'^[a-zA-Z0-9._-]+$', message='Use apenas letras, números, ponto, hífen ou sublinhado.'),
        ],
    )
    password = PasswordField(
        'Senha',
        validators=[DataRequired('Informe uma senha.'), PIN_VALIDATOR],
    )
    confirm_password = PasswordField(
        'Confirmar senha',
        validators=[DataRequired('Confirme a senha.'), EqualTo('password', message='As senhas não coincidem.')],
    )
    submit = SubmitField('Criar administrador')
