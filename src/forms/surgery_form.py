from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField, DateField, TimeField
from wtforms import BooleanField, RadioField, SubmitField
from wtforms.validators import DataRequired, Optional

class SurgeryRequestForm(FlaskForm):
    peso = FloatField('Peso (kg)', validators=[DataRequired()])
    sinais_sintomas = TextAreaField('Sinais e Sintomas Clínicos', validators=[DataRequired()])
    condicoes_justificativa = TextAreaField('Condições que Justificam a Cirurgia', validators=[DataRequired()])
    resultados_diagnosticos = TextAreaField('Resultados de Provas Diagnósticas', validators=[DataRequired()])
    
    procedimento_solicitado = SelectField('Procedimento Solicitado', validators=[DataRequired()],
                                         choices=[('', 'Selecione um procedimento'),
                                                ('Apendicectomia', 'Apendicectomia'),
                                                ('Colecistectomia', 'Colecistectomia'),
                                                ('Herniorrafia Inguinal', 'Herniorrafia Inguinal'),
                                                ('Laparotomia Exploratória', 'Laparotomia Exploratória'),
                                                ('Amidalectomia', 'Amidalectomia')])
    
    codigo_procedimento = StringField('Código do Procedimento')
    tipo_cirurgia = RadioField('Tipo de Cirurgia', validators=[DataRequired()],
                               choices=[('Eletiva', 'Eletiva'), ('Urgência', 'Urgência')])
    
    data_cirurgia = DateField('Data da Cirurgia', validators=[DataRequired()], format='%Y-%m-%d')
    internar_antes = BooleanField('Internar 1 dia antes da cirurgia')
    hora_cirurgia = TimeField('Hora da Cirurgia', validators=[DataRequired()], format='%H:%M')
    
    assistente = SelectField('Assistente', validators=[DataRequired()],
                           choices=[('', 'Selecione um assistente'),
                                  ('Dr. João Silva', 'Dr. João Silva'),
                                  ('Dra. Maria Santos', 'Dra. Maria Santos'),
                                  ('Dr. Carlos Oliveira', 'Dr. Carlos Oliveira'),
                                  ('Dra. Ana Costa', 'Dra. Ana Costa'),
                                  ('Dr. Ricardo Pereira', 'Dr. Ricardo Pereira')])
    
    aparelhos_especiais = StringField('Aparelhos Especiais', validators=[Optional()])
    reserva_sangue = BooleanField('Reserva de Sangue')
    quantidade_sangue = StringField('Quantidade Prevista', validators=[Optional()])
    raio_x = BooleanField('Raio-X')
    reserva_uti = BooleanField('Reserva de Vaga UTI')
    duracao_prevista = StringField('Duração Prevista', validators=[DataRequired()])
    
    evolucao_internacao = TextAreaField('Evolução para Internação', validators=[Optional()])
    prescricao_internacao = TextAreaField('Prescrição para Internação', validators=[Optional()])
    exames_preop = TextAreaField('Exames Pré-Operatórios', validators=[Optional()])
    opme = TextAreaField('OPME', validators=[Optional()])
    
    submit = SubmitField('Solicitar Cirurgia')