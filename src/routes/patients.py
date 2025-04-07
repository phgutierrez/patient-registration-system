from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from src.models.patient import Patient
from src.app import db

patients = Blueprint('patients', __name__)

@patients.route('/patient/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    if request.method == 'POST':
        nome = request.form.get('nome')
        
        # Verificar se o paciente já existe
        existing_patient = Patient.query.filter(Patient.nome.ilike(f'%{nome}%')).first()
        if existing_patient:
            flash('Paciente com nome similar já existe no sistema.', 'danger')
            return render_template('patient/new.html')
        
        # Converter data de nascimento para o formato do Python
        data_nascimento_str = request.form.get('data_nascimento')
        try:
            data_nascimento = datetime.strptime(data_nascimento_str, '%d/%m/%Y')
        except ValueError:
            flash('Data de nascimento inválida.', 'danger')
            return render_template('patient/new.html')
        
        # Criar novo paciente
        patient = Patient(
            nome=nome,
            prontuario=request.form.get('prontuario'),
            data_nascimento=data_nascimento,
            sexo=request.form.get('sexo'),
            nome_mae=request.form.get('nome_mae'),
            cns=request.form.get('cns'),
            cidade=request.form.get('cidade'),
            contato=request.form.get('contato'),
            diagnostico=request.form.get('diagnostico'),
            cid=request.form.get('cid')
        )
        
        try:
            db.session.add(patient)
            db.session.commit()
            flash('Paciente cadastrado com sucesso!', 'success')
            return redirect(url_for('patients.view_patient', id=patient.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar paciente: {str(e)}', 'danger')
            return render_template('patient/new.html')
    
    return render_template('patient/new.html')

@patients.route('/patients')
@login_required
def list_patients():
    patients = Patient.query.all()
    return render_template('patient/list.html', patients=patients)

@patients.route('/patient/<int:id>')
@login_required
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    return render_template('patient/view.html', patient=patient)

@patients.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    hoje = date.today()
    
    if request.method == 'POST':
        try:
            # Converte a string de data para objeto date
            data_nascimento = datetime.strptime(
                request.form.get('data_nascimento'), 
                '%Y-%m-%d'
            ).date()
            
            patient.nome = request.form.get('nome')
            patient.data_nascimento = data_nascimento
            patient.cns = request.form.get('cns')
            patient.nome_mae = request.form.get('nome_mae')
            patient.cidade = request.form.get('cidade')
            patient.endereco = request.form.get('endereco')
            patient.estado = request.form.get('estado')
            
            db.session.commit()
            flash('Paciente atualizado com sucesso!', 'success')
            return redirect(url_for('patients.view_patient', id=patient.id))
            
        except (ValueError, TypeError) as e:
            flash('Erro ao atualizar paciente. Verifique os dados informados.', 'error')
            return render_template('patient/edit.html', patient=patient), 400
            
    return render_template('patient/edit.html', patient=patient, hoje=hoje)