from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required
from src.models.patient import Patient
from src.extensions import db
from src.forms.patient_form import PatientForm
from sqlalchemy.exc import SQLAlchemyError
import pyodbc
from pathlib import Path

patients = Blueprint('patients', __name__, url_prefix='/patients')


@patients.route('/patient/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    if request.method == 'POST':
        nome = request.form.get('nome')
        
        # Verificar se o paciente já existe
        existing_patient = Patient.query.filter(
            Patient.nome.ilike(f'%{nome}%')).first()
        if existing_patient:
            flash('Paciente com nome similar já existe no sistema.', 'danger')
            return render_template('patient/new.html')
        
        # Converter data de nascimento para o formato do Python
        data_nascimento_str = request.form.get('data_nascimento')
        try:
            data_nascimento = datetime.strptime(
                data_nascimento_str, '%d/%m/%Y')
        except ValueError:
            flash('Data de nascimento inválida.', 'danger')
            return render_template('patient/new.html')
        
        # Obter endereço (opcional)
        endereco = request.form.get('endereco')

        # Criar novo paciente
        patient = Patient(
            nome=nome,
            prontuario=request.form.get('prontuario'),
            data_nascimento=data_nascimento,
            sexo=request.form.get('sexo'),
            nome_mae=request.form.get('nome_mae'),
            cns=request.form.get('cns'),
            endereco=endereco,
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
    form = PatientForm(obj=patient)
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            patient.nome = form.nome.data
            patient.prontuario = form.prontuario.data
            patient.data_nascimento = form.data_nascimento.data
            patient.sexo = form.sexo.data
            patient.cns = form.cns.data
            patient.nome_mae = form.nome_mae.data
            patient.endereco = form.endereco.data
            patient.cidade = form.cidade.data
            patient.estado = form.estado.data
            patient.contato = form.contato.data
            patient.diagnostico = form.diagnostico.data
            patient.cid = form.cid.data
            
            db.session.commit()
            flash('Paciente atualizado com sucesso!', 'success')
            return redirect(url_for('patients.view_patient', id=patient.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar paciente: {str(e)}', 'danger')

    return render_template('patient/edit.html', patient=patient, form=form)


# Rota para buscar dados do banco Access (AMBULATORIO_SERV.accdb)
@patients.route('/api/search-patient-accdb', methods=['GET'])
@login_required
def search_patient_accdb():
    """Busca dados do paciente no banco Access"""
    prontuario = request.args.get('prontuario', '').strip()
    
    if not prontuario:
        return jsonify({"error": "Prontuário não fornecido"}), 400
    
    try:
        # Caminho do arquivo Access
        db_path = Path(current_app.root_path).parent / 'src' / 'static' / 'AMBULATORIO_SERV.accdb'
        
        if not db_path.exists():
            return jsonify({"error": "Banco de dados não encontrado"}), 404
        
        # String de conexão para Access
        conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};'
        
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Buscar dados na tabela cadastro_de_pacientes
            cursor.execute('SELECT * FROM cadastro_de_pacientes WHERE prontuario = ?', prontuario)
            row = cursor.fetchone()
            
            if not row:
                cursor.close()
                conn.close()
                return jsonify({"found": False}), 200
            
            # Obter nomes das colunas
            columns = [description[0] for description in cursor.description]
            
            # Converter para dicionário
            patient_data = dict(zip(columns, row))
            
            cursor.close()
            conn.close()
            
            return jsonify({"found": True, "data": patient_data}), 200
            
        except pyodbc.Error as e:
            return jsonify({"error": f"Erro ao conectar ao banco Access: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar dados: {str(e)}"}), 500


# Nova rota para verificar a existência do paciente via API
@patients.route('/api/check-patient', methods=['GET'])
def check_patient_exists():
    patient_name = request.args.get('name')
    if not patient_name:
        return jsonify({"error": "Nome do paciente não fornecido"}), 400

    try:
        # Realiza a busca case-insensitive e ignorando espaços extras
        existing_patient = Patient.query.filter(db.func.lower(
            Patient.nome) == db.func.lower(patient_name.strip())).first()
        exists = existing_patient is not None
        return jsonify({"exists": exists})
    except SQLAlchemyError as e:
        # Logar o erro pode ser útil aqui
        print(f"Erro no banco de dados ao verificar paciente: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@patients.route('/patient/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    """Rota para excluir um paciente."""
    patient = Patient.query.get_or_404(id)
    try:
        # Aqui você pode adicionar lógica para verificar permissões
        # ou para lidar com entidades relacionadas (ex: cirurgias) antes de excluir.

        db.session.delete(patient)
        db.session.commit()
        flash(f'Paciente \"{patient.nome}\" excluído com sucesso!', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Erro ao excluir paciente: {str(e)}', 'danger')
        # Logar o erro pode ser útil aqui
        print(f"Erro ao excluir paciente ID {id}: {e}")
    except Exception as e:  # Captura outros erros inesperados
        db.session.rollback()
        flash(f'Ocorreu um erro inesperado ao excluir o paciente.', 'danger')
        print(f"Erro inesperado ao excluir paciente ID {id}: {e}")

    return redirect(url_for('patients.list_patients'))
