from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from src.models.patient import Patient
from src.extensions import db, limiter
from src.forms.patient_form import PatientForm
from src.runtime_security import ensure_patient_access, scoped_patients_query
from src.services.specialty_service import get_active_specialty
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
import time
import logging
from pathlib import Path

patients = Blueprint('patients', __name__, url_prefix='/patients')
logger = logging.getLogger(__name__)


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
        active_specialty = get_active_specialty()
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
            cid=request.form.get('cid'),
            specialty_id=current_user.specialty_id or (active_specialty.id if active_specialty else None)
        )
        
        try:
            db.session.add(patient)
            db.session.commit()
            flash('Paciente cadastrado com sucesso!', 'success')
            return redirect(url_for('patients.view_patient', id=patient.id))
        except Exception:
            db.session.rollback()
            flash('Erro ao cadastrar paciente.', 'danger')
            return render_template('patient/new.html')
    
    return render_template('patient/new.html')


@patients.route('/patients')
@login_required
def list_patients():
    search = request.args.get('q', '').strip()[:100]
    page = request.args.get('page', 1, type=int)
    page = max(page or 1, 1)
    query = scoped_patients_query(Patient.query)
    if search:
        term = f'%{search}%'
        query = query.filter(or_(
            Patient.nome.ilike(term), Patient.prontuario.ilike(term),
            Patient.cns.ilike(term), Patient.cidade.ilike(term),
        ))
    pagination = query.order_by(Patient.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        'patient/list.html', patients=pagination.items,
        pagination=pagination, search=search,
    )


@patients.route('/patient/<int:id>')
@login_required
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    access_error = ensure_patient_access(patient)
    if access_error:
        return access_error
    return render_template('patient/view.html', patient=patient)


@patients.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    access_error = ensure_patient_access(patient)
    if access_error:
        return access_error
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
            
        except Exception:
            db.session.rollback()
            flash('Erro ao atualizar paciente.', 'danger')

    return render_template('patient/edit.html', patient=patient, form=form)


# ISSUE 2: Optimized patient lookup by prontuário with performance monitoring
@patients.route('/api/search-patient-prontuario', methods=['GET'])
@login_required
@limiter.limit('20 per minute')
def search_patient_by_prontuario():
    """
    Fast patient lookup by prontuário for LAN deployment.
    Uses optimized query with timing monitoring.
    """
    prontuario = request.args.get('prontuario', '').strip()
    if not prontuario:
        return jsonify({"error": "Prontuário não fornecido"}), 400

    try:
        # ISSUE 2: Performance monitoring
        start_time = time.time()
        
        # Optimized query: use indexed column, load only required fields
        patient = scoped_patients_query(Patient.query).filter_by(prontuario=prontuario).first()
        
        query_duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        logger.debug(f"Patient prontuário lookup took {query_duration:.2f}ms")
        
        if not patient:
            return jsonify({
                "found": False, 
                "message": "Prontuário não encontrado",
                "query_time_ms": round(query_duration, 2)
            }), 404

        # Return only essential patient info (avoid relationship loading)
        patient_data = {
            'id': patient.id,
            'nome': patient.nome,
            'prontuario': patient.prontuario,
            'data_nascimento': patient.data_nascimento.isoformat() if patient.data_nascimento else None,
            'sexo': patient.sexo,
            'nome_mae': patient.nome_mae,
            'cns': patient.cns,
            'cidade': patient.cidade,
            'endereco': patient.endereco,
            'estado': patient.estado,
            'contato': patient.contato,
            'diagnostico': patient.diagnostico,
            'cid': patient.cid,
            'idade': patient.idade
        }

        return jsonify({
            "found": True,
            "data": patient_data,
            "query_time_ms": round(query_duration, 2)
        }), 200
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in prontuário search: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in prontuário search: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@patients.route('/api/search-patient-accdb', methods=['GET'])
@login_required
@limiter.limit('10 per minute')
def search_patient_accdb():
    """Busca somente leitura no Access configurado para Ortopedia."""
    from src.models.specialty import Specialty
    from src.services.access_patient_service import AccessConfig, AccessLookupError, access_patient_service

    prontuario = str(request.args.get('prontuario', '') or '').strip()
    if not prontuario:
        return jsonify({'ok': False, 'found': False, 'code': 'INVALID_PRONTUARIO', 'message': 'Informe o número do prontuário.', 'hint': 'Digite o prontuário antes de buscar.', 'data': None}), 400
    specialty = Specialty.query.filter_by(slug='ortopedia', is_active=True).first()
    settings = specialty.settings if specialty else None
    config = AccessConfig(
        host=(settings.access_host if settings else '192.168.1.252'),
        share_path=(settings.access_share_path if settings else r'naqh\AMBULATORIO_SERV'),
        filename=(settings.access_filename if settings else 'AMBULATORIO_SERV.accdb'),
        enabled=(settings.access_enabled if settings else True),
    )
    try:
        result = access_patient_service.search(config, prontuario)
        if not result['found']:
            return jsonify({
                'ok': True, 'found': False, 'code': 'PATIENT_NOT_FOUND',
                'message': 'Prontuário não localizado no banco do CPAM.',
                'hint': 'Confira o número informado ou preencha o cadastro manualmente.',
                **result,
            }), 404
        return jsonify({'ok': True, 'code': 'PATIENT_FOUND', 'message': 'Paciente encontrado.', 'hint': '', **result}), 200
    except ValueError as exc:
        current_app.logger.error('Configuração Access inválida: %s', exc)
        return jsonify({'ok': False, 'found': False, 'code': 'ACCESS_CONFIG_INVALID', 'message': 'A configuração do banco Access é inválida.', 'hint': 'Solicite ao administrador que revise as Configurações.', 'data': None}), 503
    except AccessLookupError as exc:
        current_app.logger.warning('Falha Access %s', exc.code)
        return jsonify(exc.payload()), exc.status


# Nova rota para verificar a existência do paciente via API
@patients.route('/api/check-patient', methods=['GET'])
@login_required
@limiter.limit('20 per minute')
def check_patient_exists():
    patient_name = request.args.get('name')
    if not patient_name:
        return jsonify({"error": "Nome do paciente não fornecido"}), 400

    try:
        # ISSUE 2: Performance monitoring for name search
        start_time = time.time()
        
        # Realiza a busca case-insensitive e ignorando espaços extras
        existing_patient = scoped_patients_query(Patient.query).filter(db.func.lower(
            Patient.nome) == db.func.lower(patient_name.strip())).first()
            
        query_duration = (time.time() - start_time) * 1000
        logger.debug(f"Patient name search took {query_duration:.2f}ms")
        
        exists = existing_patient is not None
        return jsonify({
            "exists": exists,
            "query_time_ms": round(query_duration, 2)
        })
    except SQLAlchemyError as e:
        # Logar o erro pode ser útil aqui
        print(f"Erro no banco de dados ao verificar paciente: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@patients.route('/patient/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    """Rota para excluir um paciente."""
    patient = Patient.query.get_or_404(id)
    access_error = ensure_patient_access(patient)
    if access_error:
        return access_error
    try:
        # Aqui você pode adicionar lógica para verificar permissões
        # ou para lidar com entidades relacionadas (ex: cirurgias) antes de excluir.
        # A relação em Patient com cascade="all, delete-orphan" automaticamente
        # deleta todas as SurgeryRequest relacionadas

        db.session.delete(patient)
        db.session.commit()
        flash(f'Paciente \"{patient.nome}\" excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        # Log detalhado do erro
        print(f"❌ Erro ao excluir paciente ID {id}: {type(e).__name__}: {str(e)}")
        # Se for erro de FK ou integridade, ofereça dica ao usuário
        if "FOREIGN KEY constraint failed" in str(e).upper() or "UNIQUE constraint failed" in str(e).upper():
            flash(f'Não é possível excluir este paciente. Ele pode estar vinculado a outras solicitações de cirurgia.', 'warning')
        else:
            flash(f'Erro ao excluir paciente: {str(e)}', 'danger')

    return redirect(url_for('patients.list_patients'))
