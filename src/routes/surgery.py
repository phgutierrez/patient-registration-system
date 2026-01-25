from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from src.models.surgery_request import SurgeryRequest
from src.models.patient import Patient
from src.extensions import db
from src.utils.pdf_utils import preencher_formulario_internacao, preencher_requisicao_hemocomponente
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
            # Criar nova solicitação de cirurgia
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
            # Commit inicial para obter o ID da cirurgia antes de gerar nome do PDF
            db.session.flush()
            db.session.refresh(surgery_request)
            surgery_request_id = surgery_request.id  # Guarda o ID

            # Gerar o PDF com os dados da solicitação
            try:
                # Passa o objeto surgery_request com ID para gerar o nome
                pdf_path = preencher_formulario_internacao(
                    patient, surgery_request)

                # Gerar PDF de requisição de hemocomponente se sangue for reservado
                pdf_hemocomponente = None
                if surgery_request.reserva_sangue:
                    try:
                        pdf_hemocomponente = preencher_requisicao_hemocomponente(
                            patient, surgery_request)
                        if pdf_hemocomponente:
                            hemo_filename = os.path.basename(pdf_hemocomponente)
                            surgery_request.pdf_hemocomponente = hemo_filename
                    except Exception as e:
                        print(f"Aviso: Erro ao gerar PDF de hemocomponente: {str(e)}")
                        # Não falha a solicitação se o PDF de hemocomponente falhar

                if pdf_path:
                    pdf_filename = os.path.basename(pdf_path)
                    # Salva o nome do arquivo no banco de dados
                    surgery_request.pdf_filename = pdf_filename
                    db.session.commit()  # Commit final com o nome do arquivo

                    # Redirecionar para a página de confirmação
                    return redirect(url_for('surgery.confirmation',
                                            surgery_id=surgery_request_id,  # Usa o ID guardado
                                            pdf_name=pdf_filename))
                else:
                    db.session.commit()  # Commita mesmo se o PDF falhar
                    flash('PDF gerado mas o caminho não foi retornado.', 'warning')
                    return redirect(url_for('patients.view_patient', id=patient.id))
            except Exception as e:
                db.session.rollback()  # Rollback se a geração do PDF falhar *após* o flush
                flash(
                    f'Solicitação registrada, mas houve um erro ao gerar o PDF: {str(e)}', 'warning')
                print(f"Erro ao gerar PDF: {str(e)}")
                return redirect(url_for('patients.view_patient', id=patient.id))

        except Exception as e:
            db.session.rollback()  # Rollback se o salvamento inicial falhar
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


@surgery.route('/surgery/debug/test-pdf-generation', methods=['GET'])
@login_required
def debug_pdf_generation():
    """Rota de debug para testar a geração do PDF"""
    try:
        # Buscar um paciente e uma cirurgia para teste
        patient = Patient.query.first()
        surgery_request = SurgeryRequest.query.first()
        
        if not patient or not surgery_request:
            return "Nenhum paciente ou solicitação de cirurgia encontrado para teste", 404
        
        # Tentar gerar o PDF
        from src.utils.pdf_utils import preencher_formulario_internacao
        pdf_path = preencher_formulario_internacao(patient, surgery_request)
        
        return f"""
        <h2>Teste de Geração de PDF</h2>
        <p><strong>Status:</strong> PDF gerado com sucesso!</p>
        <p><strong>Caminho:</strong> {pdf_path}</p>
        <p><a href="/static/preenchidos/{os.path.basename(pdf_path)}" target="_blank">Clique aqui para visualizar o PDF</a></p>
        <p><a href="javascript:history.back()">Voltar</a></p>
        """
    except Exception as e:
        import traceback
        return f"""
        <h2>Erro na Geração do PDF</h2>
        <p><strong>Erro:</strong> {str(e)}</p>
        <h3>Traceback:</h3>
        <pre>{traceback.format_exc()}</pre>
        <p><a href="javascript:history.back()">Voltar</a></p>
        """


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


@surgery.route('/surgery/<int:surgery_id>/pdf-hemocomponente/<path:pdf_name>')
@login_required
def download_pdf_hemocomponente(surgery_id, pdf_name):
    """Rota para download do PDF de requisição de hemocomponente"""
    # Verificar se o registro de cirurgia existe
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)

    # Verificar se foi solicitado reserva de sangue
    if not surgery_request.reserva_sangue:
        flash('Nenhuma reserva de sangue foi solicitada para esta cirurgia.', 'warning')
        return redirect(url_for('surgery.confirmation', surgery_id=surgery_id, pdf_name=surgery_request.pdf_filename))

    # Construir o caminho completo para o arquivo PDF
    from flask import current_app
    from pathlib import Path

    base_dir = Path(current_app.root_path)
    pdf_path = base_dir / 'static' / 'preenchidos' / pdf_name

    if not os.path.exists(pdf_path):
        flash('O arquivo PDF de hemocomponente não foi encontrado.', 'danger')
        return redirect(url_for('surgery.confirmation', surgery_id=surgery_id, pdf_name=surgery_request.pdf_filename))

    # Enviar o arquivo para download
    return send_file(pdf_path, as_attachment=True, download_name=f"Requisicao_Hemocomponente_{surgery_request.patient_id}.pdf")
