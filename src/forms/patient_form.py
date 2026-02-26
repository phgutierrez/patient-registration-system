from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class PatientForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[
                       DataRequired(), Length(min=3, max=100)])
    prontuario = StringField('Prontuário', validators=[
                             DataRequired(), Length(min=1, max=20)])
    data_nascimento = DateField('Data de Nascimento', validators=[
                                DataRequired()], format='%Y-%m-%d')
    sexo = SelectField('Sexo', choices=[
                       ('M', 'Masculino'), ('F', 'Feminino')], validators=[DataRequired()])
    cns = StringField('CNS', validators=[
                      DataRequired(), Length(min=15, max=15)])
    nome_mae = StringField('Nome da Mãe', validators=[
                           DataRequired(), Length(min=3, max=100)])
    endereco = StringField('Endereço', validators=[
                           DataRequired(), Length(min=5, max=200)])
    cidade = StringField('Cidade', validators=[
                         DataRequired(), Length(min=2, max=100)])
    estado = StringField('Estado', validators=[
                         DataRequired(), Length(min=2, max=2)])
    contato = StringField('Contato', validators=[
                          DataRequired(), Length(min=10, max=15)])
    diagnostico = TextAreaField('Diagnóstico', validators=[DataRequired()])
    cid = StringField('CID', validators=[DataRequired(), Length(min=3, max=4)])
