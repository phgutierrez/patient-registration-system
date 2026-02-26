from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional, Length, Regexp


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
