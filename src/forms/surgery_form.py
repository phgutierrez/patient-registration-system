from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField, DateField, TimeField
from wtforms import BooleanField, RadioField, SubmitField
from wtforms.validators import DataRequired, Optional


class SurgeryRequestForm(FlaskForm):
    peso = FloatField('Peso (kg)', validators=[DataRequired()])
    sinais_sintomas = TextAreaField(
        'Sinais e Sintomas Clínicos', validators=[DataRequired()])
    condicoes_justificativa = TextAreaField(
        'Condições que Justificam a Cirurgia', validators=[DataRequired()])
    resultados_diagnosticos = TextAreaField(
        'Resultados de Provas Diagnósticas', validators=[DataRequired()])

    procedimento_solicitado = SelectField('Procedimento Solicitado', validators=[DataRequired()],
                                          choices=[
        ('', 'Selecione um procedimento'),
        ('Epifisiodese femoral proximal in situ',
         'Epifisiodese femoral proximal in situ'),
        ('Osteotomia da Pelve',
         'Osteotomia da Pelve'),
        ('Realinhamento do mecanismo extensor do joelho',
         'Realinhamento do mecanismo extensor do joelho'),
        ('Redução Incruenta de Luxação congênita coxofemoral',
         'Redução Incruenta de Luxação congênita coxofemoral'),
        ('Revisão cirúrgica do Pé torto congênito',
         'Revisão cirúrgica do Pé torto congênito'),
        ('Tratamento cirúrgico de luxação coxofemoral congenita',
         'Tratamento cirúrgico de luxação coxofemoral congenita'),
        ('Tratamento cirúrgico de luxação espontânea / progressiva / paralitica do quadril',
         'Tratamento cirúrgico de luxação espontânea / progressiva / paralitica do quadril'),
        ('Talectomia', 'Talectomia'),
        ('Tratamento cirúrgico de coalizão tarsal',
         'Tratamento cirúrgico de coalizão tarsal'),
        ('Tratamento cirúrgico de pé cavo',
         'Tratamento cirúrgico de pé cavo'),
        ('Tratamento cirúrgico de pé plano valgo',
         'Tratamento cirúrgico de pé plano valgo'),
        ('Tratamento cirúrgico de pé torto congênito',
         'Tratamento cirúrgico de pé torto congênito'),
        ('Tratamento cirúrgico de pé torto congênito inveterado',
         'Tratamento cirúrgico de pé torto congênito inveterado'),
        ('Tratamento cirúrgico de pseudoartrose congênita da tibia',
         'Tratamento cirúrgico de pseudoartrose congênita da tibia'),
        ('Alongamento / Encurtamento miotendinoso',
         'Alongamento / Encurtamento miotendinoso'),
        ('Osteotomia de ossos longos exceto da mão e do pé',
         'Osteotomia de ossos longos exceto da mão e do pé'),
        ('Ressecção de cisto sinovial',
         'Ressecção de cisto sinovial'),
        ('Retirada de fio ou pino intra-ósseo',
         'Retirada de fio ou pino intra-ósseo'),
        ('Retirada de Fixador externo',
         'Retirada de Fixador externo'),
        ('Retirada de Placa e/ou parafusos',
         'Retirada de Placa e/ou parafusos'),
        ('Transposição / Transferência miotendinosa única',
         'Transposição / Transferência miotendinosa única'),
        ('Neurolise não funcional',
         'Neurolise não funcional')
    ])

    codigo_procedimento = StringField('Código do Procedimento')
    tipo_cirurgia = RadioField('Tipo de Cirurgia', validators=[DataRequired()],
                               choices=[('Eletiva', 'Eletiva'), ('Urgência', 'Urgência')])

    data_cirurgia = DateField('Data da Cirurgia', validators=[
                              DataRequired()], format='%Y-%m-%d')
    internar_antes = BooleanField('Internar 1 dia antes da cirurgia')
    hora_cirurgia = TimeField('Hora da Cirurgia', validators=[
                              DataRequired()], format='%H:%M')

    assistente = SelectField('Assistente', validators=[DataRequired()],
                             choices=[('', 'Selecione um assistente'),
                                      ('Dr. Francisco Laecio',
                                       'Dr. Francisco Laecio'),
                                      ('Dr. Brauner Cavalcanti',
                                       'Dr. Brauner Cavalcanti'),
                                      ('Dr. André Cristiano',
                                       'Dr. André Cristiano'),
                                      ('Dr. Sávio Bruno', 'Dr. Sávio Bruno'),
                                      ('Dr. Bruno Montenegro',
                                       'Dr. Bruno Montenegro'),
                                      ('Dr. Luiz Eduardo Portela',
                                       'Dr. Luiz Eduardo Portela'),
                                      ('Dr. Jocemir Paulino', 'Dr. Jocemir Paulino')])

    aparelhos_especiais = StringField(
        'Aparelhos Especiais', validators=[Optional()])
    reserva_sangue = BooleanField('Reserva de Sangue')
    quantidade_sangue = StringField(
        'Quantidade Prevista', validators=[Optional()])
    raio_x = BooleanField('Raio-X')
    reserva_uti = BooleanField('Reserva de Vaga UTI')
    duracao_prevista = StringField(
        'Duração Prevista', validators=[DataRequired()])

    evolucao_internacao = TextAreaField(
        'Evolução para Internação', validators=[Optional()])
    prescricao_internacao = TextAreaField(
        'Prescrição para Internação', validators=[Optional()])
    exames_preop = TextAreaField(
        'Exames Pré-Operatórios', validators=[Optional()])
    opme = TextAreaField('OPME', validators=[Optional()])

    submit = SubmitField('Solicitar Cirurgia')
