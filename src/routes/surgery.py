from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from src.models.surgery_request import SurgeryRequest
from src.models.patient import Patient
from src.app import db
from src.utils.pdf_utils import preencher_formulario_internacao
from src.forms.surgery_form import SurgeryRequestForm
from datetime import datetime
import os

surgery = Blueprint('surgery', __name__)

@surgery.route('/patient/<int:patient_id>/surgery/request', methods=['GET', 'POST'])
@login_required
def request_surgery(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = SurgeryRequestForm()
    
    if form.validate_on_submit():
        try:
            # Criar nova solicitação de cirurgia a partir dos dados do formulário
            surgery_request = SurgeryRequest(
                patient_id=patient.id,
                peso=form.peso.data,
                sinais_sintomas=form.sinais_sintomas.data,
                condicoes_justificativa=form.condicoes_justificativa.data,
                resultados_diagnosticos=form.resultados_diagnosticos.data,
                procedimento_solicitado=form.procedimento_solicitado.data,
                codigo_procedimento=form.codigo_procedimento.data,
                tipo_cirurgia=form.tipo_cirurgia.data,
                data_cirurgia=form.data_cirurgia.data,
                internar_antes=form.internar_antes.data,
                hora_cirurgia=form.hora_cirurgia.data,
                assistente=form.assistente.data,
                aparelhos_especiais=form.aparelhos_especiais.data,
                reserva_sangue=form.reserva_sangue.data,
                quantidade_sangue=form.quantidade_sangue.data if form.reserva_sangue.data else None,
                raio_x=form.raio_x.data,
                reserva_uti=form.reserva_uti.data,
                duracao_prevista=form.duracao_prevista.data,
                evolucao_internacao=form.evolucao_internacao.data,
                prescricao_internacao=form.prescricao_internacao.data,
                exames_preop=form.exames_preop.data,
                opme=form.opme.data
            )
            
            db.session.add(surgery_request)
            db.session.commit()
            
            # Gerar o PDF com os dados da solicitação
            try:
                pdf_path = preencher_formulario_internacao(patient, surgery_request)
                
                # Verificar se o caminho do PDF foi retornado corretamente
                if pdf_path:
                    # Extrair apenas o nome do arquivo do caminho completo
                    pdf_filename = os.path.basename(pdf_path)
                    
                    # Redirecionar para a página de confirmação ao invés do download direto
                    return redirect(url_for('surgery.confirmation', 
                                          surgery_id=surgery_request.id,
                                          pdf_name=pdf_filename))
                else:
                    flash('PDF gerado mas o caminho não foi retornado.', 'warning')
                    return redirect(url_for('patients.view_patient', id=patient.id))
            except Exception as e:
                flash(f'Solicitação registrada, mas houve um erro ao gerar o PDF: {str(e)}', 'warning')
                print(f"Erro ao gerar PDF: {str(e)}")
                return redirect(url_for('patients.view_patient', id=patient.id))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar solicitação: {str(e)}', 'danger')
            print(f"Erro ao salvar solicitação: {str(e)}")
    
    return render_template('surgery/request.html', patient=patient, form=form)

# Nova rota para página de confirmação
@surgery.route('/surgery/<int:surgery_id>/confirmation/<path:pdf_name>')
@login_required
def confirmation(surgery_id, pdf_name):
    # Verificar se o registro de cirurgia existe
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    patient = Patient.query.get_or_404(surgery_request.patient_id)
    
    return render_template('surgery/confirmation.html', 
                           surgery=surgery_request, 
                           patient=patient,
                           pdf_name=pdf_name)

@surgery.route('/surgery/<int:surgery_id>/pdf/<path:pdf_name>')
@login_required
def download_pdf(surgery_id, pdf_name):
    # Verificar se o registro de cirurgia existe
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    
    # Construir o caminho completo para o arquivo PDF
    from flask import current_app
    from pathlib import Path
    
    base_dir = Path(current_app.root_path)
    pdf_path = base_dir / 'static' / 'preenchidos' / pdf_name
    
    if not os.path.exists(pdf_path):
        flash('O arquivo PDF não foi encontrado.', 'danger')
        return redirect(url_for('patients.view_patient', id=surgery_request.patient_id))
    
    # Enviar o arquivo para download
    return send_file(pdf_path, as_attachment=True, download_name=f"Internacao_{surgery_request.patient_id}.pdf")