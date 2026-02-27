"""
Formulário de solicitação de cirurgia.

Os choices de procedimento_solicitado e assistente são injetados
dinamicamente pela rota, baseados na especialidade ativa.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, TextAreaField, SelectField,
    DateField, TimeField, BooleanField, RadioField, SubmitField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import ListWidget, CheckboxInput

OPME_CHOICES = [
    ('Ilizarov Adulto', 'Ilizarov Adulto'),
    ('Ilizarov Infantil', 'Ilizarov Infantil'),
    ('Caixa 3,5mm', 'Caixa 3,5mm'),
    ('Caixa 4,5mm', 'Caixa 4,5mm'),
    ('Placa angulada', 'Placa angulada'),
    ('Fios de Kirschner', 'Fios de Kirschner'),
    ('Parafuso Canulado', 'Parafuso Canulado'),
    ('Âncora', 'Âncora'),
    ('Placa em 8', 'Placa em 8'),
    ('Artrodese Coluna', 'Artrodese Coluna'),
    ('Não se aplica', 'Não se aplica'),
]


class SurgeryRequestForm(FlaskForm):
    # ── Dados Clínicos ────────────────────────────────────────────────────
    peso = FloatField('Peso (kg)', validators=[DataRequired()])
    sinais_sintomas = TextAreaField(
        'Sinais e Sintomas Clínicos', validators=[DataRequired()])
    condicoes_justificativa = TextAreaField(
        'Condições que Justificam a Cirurgia', validators=[DataRequired()])
    resultados_diagnosticos = TextAreaField(
        'Resultados de Provas Diagnósticas', validators=[DataRequired()])

    # ── Procedimento — choices injetados dinamicamente pela rota ──────────
    procedimento_solicitado = SelectField(
        'Procedimento Solicitado',
        validators=[DataRequired()],
        choices=[('', 'Selecione um procedimento')],
        validate_choice=False,
    )
    codigo_procedimento = StringField('Código do Procedimento')

    tipo_cirurgia = RadioField(
        'Tipo de Cirurgia',
        validators=[DataRequired()],
        choices=[('Eletiva', 'Eletiva'), ('Urgência', 'Urgência')],
    )
    data_cirurgia = DateField('Data da Cirurgia', validators=[DataRequired()], format='%Y-%m-%d')
    internar_antes = BooleanField('Internar 1 dia antes da cirurgia')
    hora_cirurgia = TimeField('Hora da Cirurgia', validators=[DataRequired()], format='%H:%M')

    # ── Assistente — choices injetados dinamicamente pela rota ────────────
    assistente = SelectField(
        'Assistente',
        validators=[DataRequired()],
        choices=[('', 'Selecione um assistente')],
        validate_choice=False,
    )

    # ── Recursos ─────────────────────────────────────────────────────────
    aparelhos_especiais = StringField('Aparelhos Especiais', validators=[Optional()])
    reserva_sangue = BooleanField('Reserva de Sangue')
    quantidade_sangue = StringField('Quantidade Prevista', validators=[Optional()])
    raio_x = BooleanField('Raio-X')
    reserva_uti = BooleanField('Reserva de Vaga UTI')
    duracao_prevista = StringField('Duração Prevista', validators=[DataRequired()])

    # ── Informações para Internação ───────────────────────────────────────
    evolucao_internacao = TextAreaField('Evolução para Internação', validators=[Optional()])
    prescricao_internacao = TextAreaField('Prescrição para Internação', validators=[Optional()])
    exames_preop = TextAreaField('Exames Pré-Operatórios', validators=[Optional()])

    # ── OPME (checkboxes + campo livre) ──────────────────────────────────
    # Compatibilidade com template legado que ainda usa textarea `opme`.
    opme = TextAreaField('OPME', validators=[Optional()])
    opme_items = SelectMultipleField(
        'OPME',
        validators=[Optional()],
        choices=OPME_CHOICES,
        widget=ListWidget(prefix_label=False),
        option_widget=CheckboxInput(),
    )
    opme_outro = StringField('Outro (OPME)', validators=[Optional()])

    submit = SubmitField('Solicitar Cirurgia')

