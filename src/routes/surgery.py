from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from src.models.surgery_request import SurgeryRequest
from src.models.patient import Patient
from src.extensions import db, limiter
from src.utils.pdf_utils import preencher_formulario_internacao, preencher_requisicao_hemocomponente
from src.forms.surgery_form import SurgeryRequestForm
from src.runtime_security import (
    ensure_patient_access,
    ensure_surgery_access,
    get_protected_pdf_path,
    require_admin,
)
from src.services.specialty_service import (
    get_active_specialty, get_procedure_choices, get_user_choices,
    get_procedure_code_map, get_sus_code_for_procedure, get_specialty_settings,
)
from datetime import datetime
import os
import logging
import json
import unicodedata
import re

surgery = Blueprint('surgery', __name__)
logger = logging.getLogger(__name__)


def _normalize_text(value):
    """Normaliza texto para comparação sem acentos/case."""
    if not value:
        return ''
    text = unicodedata.normalize('NFKD', str(value))
    return ''.join(ch for ch in text if not unicodedata.combining(ch)).strip().lower()


def _is_nao_se_aplica(value):
    return _normalize_text(value) == 'nao se aplica'


def _build_opme_value(form):
    """
    Constrói o valor textual de OPME.
    Regra: se OPME for apenas 'Não se aplica', retorna None para não imprimir no PDF.
    """
    selected_items = [item.strip() for item in (form.opme_items.data or []) if item and item.strip()]
    other_text = (form.opme_outro.data or '').strip()

    # Fallback legado para textarea opme, se os novos campos vierem vazios
    if not selected_items and not other_text and getattr(form, 'opme', None) and form.opme.data:
        legacy_value = form.opme.data.strip()
        return None if _is_nao_se_aplica(legacy_value) else legacy_value

    selected_items = [item for item in selected_items if not _is_nao_se_aplica(item)]
    parts = [*selected_items]
    if other_text:
        parts.append(f'Outro: {other_text}')
    # Separador com baixa chance de colisão com descrições que contêm vírgula.
    return ' | '.join(parts) or None


def _prefill_opme_fields(form, surgery_request):
    """Preenche opme_items/opme_outro a partir do texto salvo no banco."""
    raw_value = (surgery_request.opme or '').strip()
    if not raw_value or _is_nao_se_aplica(raw_value):
        form.opme_items.data = []
        form.opme_outro.data = ''
        if getattr(form, 'opme', None):
            form.opme.data = ''
        return

    known_choices = [choice_value for choice_value, _ in form.opme_items.choices]
    selected = []
    other_parts = []

    # Formato novo (separado por " | ")
    if ' | ' in raw_value:
        tokens = [token.strip() for token in raw_value.split(' | ') if token and token.strip()]
        for token in tokens:
            if token in known_choices and not _is_nao_se_aplica(token):
                selected.append(token)
                continue
            if token.lower().startswith('outro:'):
                value = token.split(':', 1)[1].strip()
                if value:
                    other_parts.append(value)
                continue
            if not _is_nao_se_aplica(token):
                other_parts.append(token)
    else:
        # Formato legado: pode estar separado por vírgula e conter itens com vírgula no texto.
        legacy_text = raw_value
        outro_match = re.search(r'Outro:\s*(.+)$', legacy_text, flags=re.IGNORECASE)
        if outro_match:
            outro_value = outro_match.group(1).strip(' ,|')
            if outro_value:
                other_parts.append(outro_value)
            legacy_text = legacy_text[:outro_match.start()].strip(' ,|')

        # Detecta os itens conhecidos por presença textual
        for choice in sorted(known_choices, key=len, reverse=True):
            if choice and choice in legacy_text and not _is_nao_se_aplica(choice):
                selected.append(choice)
                legacy_text = legacy_text.replace(choice, ' ')

        leftovers = legacy_text.replace(',', ' ').replace('|', ' ').strip()
        leftovers = ' '.join(leftovers.split())
        if leftovers and not _is_nao_se_aplica(leftovers):
            other_parts.append(leftovers)

    form.opme_items.data = selected
    form.opme_outro.data = ', '.join(other_parts)
    if getattr(form, 'opme', None):
        form.opme.data = raw_value


def _apply_form_to_surgery_request(surgery_request, form, specialty, sus_code, opme_value):
    surgery_request.specialty_id = specialty.id if specialty else None
    surgery_request.peso = form.peso.data
    surgery_request.sinais_sintomas = form.sinais_sintomas.data
    surgery_request.condicoes_justificativa = form.condicoes_justificativa.data
    surgery_request.resultados_diagnosticos = form.resultados_diagnosticos.data
    surgery_request.procedimento_solicitado = form.procedimento_solicitado.data
    surgery_request.codigo_procedimento = sus_code
    surgery_request.tipo_cirurgia = form.tipo_cirurgia.data
    surgery_request.data_cirurgia = form.data_cirurgia.data
    surgery_request.internar_antes = form.internar_antes.data
    surgery_request.hora_cirurgia = form.hora_cirurgia.data
    surgery_request.assistente = form.assistente.data
    surgery_request.aparelhos_especiais = form.aparelhos_especiais.data
    surgery_request.reserva_sangue = form.reserva_sangue.data
    surgery_request.quantidade_sangue = form.quantidade_sangue.data if form.reserva_sangue.data else None
    surgery_request.raio_x = form.raio_x.data
    surgery_request.reserva_uti = form.reserva_uti.data
    surgery_request.duracao_prevista = form.duracao_prevista.data
    surgery_request.evolucao_internacao = form.evolucao_internacao.data
    surgery_request.prescricao_internacao = form.prescricao_internacao.data
    surgery_request.exames_preop = form.exames_preop.data
    surgery_request.opme = opme_value


def _safe_remove_generated_file(filename):
    if not filename:
        return
    try:
        file_path = get_protected_pdf_path(filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Não foi possível remover arquivo antigo '{filename}': {e}")


def _confirmation_redirect(surgery_request):
    return redirect(url_for('surgery.confirmation', surgery_id=surgery_request.id))


def _send_authorized_pdf(surgery_request, filename, download_name, *, as_attachment):
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error

    if not filename:
        flash('O arquivo PDF não foi encontrado.', 'danger')
        return redirect(url_for('patients.view_patient', id=surgery_request.patient_id))

    pdf_path = get_protected_pdf_path(filename)
    if not pdf_path.exists():
        flash('O arquivo PDF não foi encontrado.', 'danger')
        return redirect(url_for('patients.view_patient', id=surgery_request.patient_id))

    return send_file(pdf_path, as_attachment=as_attachment, download_name=download_name)


@surgery.route('/patient/<int:patient_id>/surgery/request', methods=['GET', 'POST'])
@login_required
def request_surgery(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    access_error = ensure_patient_access(patient)
    if access_error:
        return access_error

    form = SurgeryRequestForm()

    # Carregar especialidade ativa e injetar choices
    specialty = get_active_specialty()
    form.procedimento_solicitado.choices = get_procedure_choices(specialty)
    form.assistente.choices = get_user_choices(specialty)
    procedure_code_map = get_procedure_code_map(specialty)

    if form.validate_on_submit():
        # Derivar código SUS do banco (não aceitar apenas o que veio do form)
        sus_code = (
            form.codigo_procedimento.data
            or get_sus_code_for_procedure(form.procedimento_solicitado.data, specialty)
        )
        opme_value = _build_opme_value(form)

        try:
            # Criar nova solicitação de cirurgia
            surgery_request = SurgeryRequest(patient_id=patient.id)
            _apply_form_to_surgery_request(surgery_request, form, specialty, sus_code, opme_value)
            surgery_request.created_by_user_id = current_user.id
            if specialty and not patient.specialty_id:
                patient.specialty_id = specialty.id

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
                                            surgery_id=surgery_request_id))
                else:
                    db.session.commit()  # Commita mesmo se o PDF falhar
                    flash('PDF gerado mas o caminho não foi retornado.', 'warning')
                    return redirect(url_for('patients.view_patient', id=patient.id))
            except Exception as e:
                db.session.rollback()  # Rollback se a geração do PDF falhar *após* o flush
                flash('Solicitação registrada, mas houve um erro ao gerar o PDF.', 'warning')
                logger.exception("Erro ao gerar PDF")
                return redirect(url_for('patients.view_patient', id=patient.id))

        except Exception as e:
            db.session.rollback()  # Rollback se o salvamento inicial falhar
            flash('Erro ao registrar solicitação.', 'danger')
            logger.exception("Erro ao salvar solicitação")

    return render_template(
        'surgery/request.html',
        patient=patient,
        form=form,
        specialty=specialty,
        procedure_code_map=procedure_code_map,
        is_edit_mode=False,
        surgery_request=None,
    )


@surgery.route('/surgery/<int:surgery_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_surgery_request(surgery_id):
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error
    patient = Patient.query.get_or_404(surgery_request.patient_id)

    form = SurgeryRequestForm(obj=surgery_request)

    specialty = surgery_request.specialty or get_active_specialty()
    form.procedimento_solicitado.choices = get_procedure_choices(specialty)
    form.assistente.choices = get_user_choices(specialty)
    procedure_code_map = get_procedure_code_map(specialty)

    if request.method == 'GET':
        _prefill_opme_fields(form, surgery_request)

    if form.validate_on_submit():
        sus_code = (
            form.codigo_procedimento.data
            or get_sus_code_for_procedure(form.procedimento_solicitado.data, specialty)
        )
        opme_value = _build_opme_value(form)

        try:
            old_pdf_filename = surgery_request.pdf_filename
            old_hemo_filename = surgery_request.pdf_hemocomponente

            _apply_form_to_surgery_request(surgery_request, form, specialty, sus_code, opme_value)
            db.session.flush()

            # Regenerar PDF principal para a mesma solicitação (substituição)
            pdf_path = preencher_formulario_internacao(patient, surgery_request)
            if pdf_path:
                new_pdf_filename = os.path.basename(pdf_path)
                surgery_request.pdf_filename = new_pdf_filename
                if old_pdf_filename and old_pdf_filename != new_pdf_filename:
                    _safe_remove_generated_file(old_pdf_filename)

            # Regenerar PDF de hemocomponente, quando aplicável
            if surgery_request.reserva_sangue:
                try:
                    pdf_hemocomponente = preencher_requisicao_hemocomponente(patient, surgery_request)
                    surgery_request.pdf_hemocomponente = (
                        os.path.basename(pdf_hemocomponente) if pdf_hemocomponente else None
                    )
                    if (
                        old_hemo_filename
                        and surgery_request.pdf_hemocomponente
                        and old_hemo_filename != surgery_request.pdf_hemocomponente
                    ):
                        _safe_remove_generated_file(old_hemo_filename)
                except Exception as e:
                    logger.warning(f"Erro ao regenerar PDF de hemocomponente na edição: {e}")
            else:
                surgery_request.pdf_hemocomponente = None
                _safe_remove_generated_file(old_hemo_filename)

            db.session.commit()
            flash('Solicitação atualizada com sucesso. PDF de internação substituído.', 'success')
            if surgery_request.pdf_filename:
                return _confirmation_redirect(surgery_request)
            return redirect(url_for('patients.view_patient', id=patient.id))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar solicitação.', 'danger')
            logger.exception("Erro ao editar solicitação de cirurgia")

    return render_template(
        'surgery/request.html',
        patient=patient,
        form=form,
        specialty=specialty,
        procedure_code_map=procedure_code_map,
        is_edit_mode=True,
        surgery_request=surgery_request,
    )

# Nova rota para página de confirmação


@surgery.route('/surgery/<int:surgery_id>/confirmation')
@login_required
def confirmation(surgery_id):
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error
    patient = Patient.query.get_or_404(surgery_request.patient_id)

    # Usar a especialidade gravada na própria solicitação para evitar inconsistências
    sp = surgery_request.specialty or get_active_specialty()
    settings = get_specialty_settings(sp)
    
    # ───────────────────────────────────────────────────────────────────
    # VALIDAÇÃO: Verificar se formulário Google Forms está configurado
    # ───────────────────────────────────────────────────────────────────
    forms_configured = settings and settings.forms_url
    forms_error = None
    
    if not forms_configured:
        forms_error = f'Formulário Google Forms não configurado para {sp.name}. Administrador: Configure o link do formulário nas <a href="/configuracoes/">Configurações de Especialidade</a>.'

    return render_template('surgery/confirmation.html',
                           surgery=surgery_request,
                           patient=patient,
                           specialty=sp,
                           specialty_settings=settings,
                           forms_configured=forms_configured,
                           forms_error=forms_error)


@surgery.route('/surgery/<int:surgery_id>/confirmation/<path:pdf_name>')
@login_required
def confirmation_legacy(surgery_id, pdf_name):
    return redirect(url_for('surgery.confirmation', surgery_id=surgery_id))


@surgery.route('/surgery/debug/test-pdf-generation', methods=['GET'])
@login_required
@require_admin
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
        <p><a href="{url_for('surgery.view_pdf', surgery_id=surgery_request.id)}" target="_blank">Clique aqui para visualizar o PDF</a></p>
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


@surgery.route('/surgery/<int:surgery_id>/pdf')
@login_required
@limiter.limit('30 per hour')
def download_pdf(surgery_id):
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    return _send_authorized_pdf(
        surgery_request,
        surgery_request.pdf_filename,
        f"Internacao_{surgery_request.patient_id}.pdf",
        as_attachment=True,
    )

@surgery.route('/surgery/<int:surgery_id>/pdf/<path:pdf_name>')
@login_required
def download_pdf_legacy(surgery_id, pdf_name):
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    if surgery_request.pdf_filename != os.path.basename(pdf_name):
        flash('O arquivo PDF solicitado não corresponde à solicitação.', 'danger')
        return redirect(url_for('patients.view_patient', id=surgery_request.patient_id))
    return redirect(url_for('surgery.download_pdf', surgery_id=surgery_id))


@surgery.route('/surgery/<int:surgery_id>/pdf/view')
@login_required
@limiter.limit('30 per hour')
def view_pdf(surgery_id):
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    return _send_authorized_pdf(
        surgery_request,
        surgery_request.pdf_filename,
        f"Internacao_{surgery_request.patient_id}.pdf",
        as_attachment=False,
    )


@surgery.route('/surgery/<int:surgery_id>/pdf-hemocomponente')
@login_required
@limiter.limit('20 per hour')
def download_pdf_hemocomponente(surgery_id):
    """Rota para download do PDF de requisição de hemocomponente"""
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error

    if not surgery_request.reserva_sangue:
        flash('Nenhuma reserva de sangue foi solicitada para esta cirurgia.', 'warning')
        return _confirmation_redirect(surgery_request)

    return _send_authorized_pdf(
        surgery_request,
        surgery_request.pdf_hemocomponente,
        f"Requisicao_Hemocomponente_{surgery_request.patient_id}.pdf",
        as_attachment=True,
    )


@surgery.route('/surgery/<int:surgery_id>/pdf-hemocomponente/<path:pdf_name>')
@login_required
def download_pdf_hemocomponente_legacy(surgery_id, pdf_name):
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    if surgery_request.pdf_hemocomponente != os.path.basename(pdf_name):
        flash('O arquivo PDF solicitado não corresponde à solicitação.', 'danger')
        return _confirmation_redirect(surgery_request)
    return redirect(url_for('surgery.download_pdf_hemocomponente', surgery_id=surgery_id))


@surgery.route('/surgery/<int:surgery_id>/pdf-hemocomponente/view')
@login_required
@limiter.limit('20 per hour')
def view_pdf_hemocomponente(surgery_id):
    surgery_request = SurgeryRequest.query.get_or_404(surgery_id)
    if not surgery_request.reserva_sangue:
        flash('Nenhuma reserva de sangue foi solicitada para esta cirurgia.', 'warning')
        return _confirmation_redirect(surgery_request)
    return _send_authorized_pdf(
        surgery_request,
        surgery_request.pdf_hemocomponente,
        f"Requisicao_Hemocomponente_{surgery_request.patient_id}.pdf",
        as_attachment=False,
    )


@surgery.route('/surgery_requests/<int:id>/schedule/preview', methods=['GET'])
@login_required
def schedule_preview(id):
    """
    Retorna JSON com preview do agendamento antes de confirmar.
    Agora usa submissão ao Google Forms ao invés de Web App.
    """
    from src.services.forms_service import build_forms_payload
    
    try:
        # Buscar solicitação e paciente
        surgery_request = SurgeryRequest.query.get_or_404(id)
        access_error = ensure_surgery_access(surgery_request)
        if access_error:
            return access_error
        patient = Patient.query.get_or_404(surgery_request.patient_id)
        
        # Verificar se já foi agendado
        already_scheduled = surgery_request.calendar_status == 'agendado'
        
        # Montar payload do Forms
        try:
            payload = build_forms_payload(surgery_request, patient)
            
            # Formatar preview para exibição
            preview = {
                'title': payload['procedure_title'],
                'date_display': payload['date'],
                'orthopedist': payload['orthopedist'],
                'needs_icu_display': payload['needs_icu'],
                'opme_display': ', '.join(payload['opme']) if payload['opme'] else 'Não',
                'description': payload['full_description'],
                'all_day': True
            }
            
            return jsonify({
                'ok': True,
                'preview': preview,
                'already_scheduled': already_scheduled,
                'scheduled_at': surgery_request.scheduled_at.isoformat() if surgery_request.scheduled_at else None,
                'event_link': surgery_request.scheduled_event_link
            })
            
        except ValueError as e:
            # Validação falhou (campos obrigatórios faltando)
            return jsonify({
                'ok': False,
                'message': f'Dados incompletos: {str(e)}'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao gerar preview de agendamento: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'message': f'Erro ao gerar preview: {str(e)}'
        }), 500


@surgery.route('/surgery_requests/<int:id>/schedule/confirm', methods=['POST'])
@login_required
@limiter.limit('10 per hour')
def schedule_confirm(id):
    """
    Confirma e envia agendamento submetendo resposta ao Google Forms.
    O Apps Script da planilha (onFormSubmit) criará o evento no calendário.
    """
    from src.services.forms_service import build_forms_payload, submit_form, get_forms_configuration
    
    try:
        # Buscar solicitação e paciente
        surgery_request = SurgeryRequest.query.get_or_404(id)
        access_error = ensure_surgery_access(surgery_request)
        if access_error:
            return access_error
        patient = Patient.query.get_or_404(surgery_request.patient_id)
        
        # Verificar se já foi agendado
        if surgery_request.calendar_status == 'agendado':
            return jsonify({
                'ok': False,
                'message': 'Esta cirurgia já foi agendada anteriormente',
                'event_link': surgery_request.scheduled_event_link
            }), 400
        
        # ISSUE 1 FIX: Use new configuration resolution with defaults
        try:
            public_id, view_url = get_forms_configuration()
            logger.info(f"Using Forms configuration: {public_id[:8]}...")
        except ValueError as e:
            logger.error(f"Forms configuration error: {e}")
            return jsonify({
                'ok': False,
                'message': 'Configuração do Google Forms indisponível para esta especialidade.'
            }), 500
        
        # Timeout configurável
        timeout = current_app.config.get('GOOGLE_FORMS_TIMEOUT', 10)
        
        # Montar payload
        try:
            payload = build_forms_payload(surgery_request, patient)
        except ValueError as e:
            return jsonify({
                'ok': False,
                'message': f'Dados incompletos: {str(e)}'
            }), 400
        
        # Determinar public_id para submissão
        form_public_id = None
        if public_id:
            form_public_id = public_id
        else:
            # tentar extrair do view_url
            import re
            m = re.search(r"/d/e/([A-Za-z0-9_-]+)/", view_url or '')
            if m:
                form_public_id = m.group(1)

        # Submeter ao Google Forms
        success, message, status_code = submit_form(form_public_id, payload, timeout)

        if success:
            # Atualizar registro com dados do agendamento
            surgery_request.calendar_status = 'agendado'
            surgery_request.scheduled_at = datetime.utcnow()
            
            # Não temos event_id/link direto (será criado pelo Apps Script da planilha)
            # Mas podemos adicionar link para o Forms ou deixar None
            surgery_request.scheduled_event_link = None  # Será criado pelo Apps Script
            
            db.session.commit()
            
            logger.info(f"Cirurgia {id} enviada ao Google Forms com sucesso")
            
            return jsonify({
                'ok': True,
                'message': 'Agendamento enviado com sucesso! O evento será criado automaticamente no Google Calendar.',
                'scheduledAt': surgery_request.scheduled_at.isoformat()
            })
        else:
            # Salvar status de erro
            surgery_request.calendar_status = 'erro'
            db.session.commit()
            logger.error(f"Falha ao enviar cirurgia {id} ao Forms: {message} (status {status_code})")

            # Se o erro foi de configuração do Forms (400 no service), retornar 400
            if status_code == 400:
                return jsonify({
                    'ok': False,
                    'message': message
                }), 400

            # Erros do Forms (400/403/404) - mapear para 502 Bad Gateway
            if status_code in (400, 403, 404, 502):
                return jsonify({
                    'ok': False,
                    'message': message
                }), 502

            # Outros erros: retornar 502 para falha externa
            return jsonify({
                'ok': False,
                'message': f'Falha ao enviar: {message}'
            }), 502
            
    except Exception as e:
        logger.error(f"Erro ao confirmar agendamento: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'message': 'Erro inesperado ao confirmar o agendamento.'
        }), 500


@surgery.route('/surgery_requests/debug/forms-mapping', methods=['GET'])
@login_required
@require_admin
def debug_forms_mapping():
    """Rota de debug para diagnosticar problemas no mapeamento do Forms"""
    from src.services.forms_service import get_public_form_html, extract_entry_ids, get_or_refresh_mapping, get_forms_configuration
    
    # ISSUE 1 FIX: Use new configuration resolution with defaults
    try:
        form_id, view_url = get_forms_configuration()
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': f'Forms configuration error: {str(e)}',
            'steps': []
        }), 500
        
    force_refresh = request.args.get('force', 'false').lower() == 'true'
    
    debug_info = {
        'form_id': form_id,
        'view_url': view_url,
        'force_refresh': force_refresh,
        'status': 'debug', 
        'steps': []
    }
    
    try:
        # Passo 1: Verificar se form_id está configurado
        debug_info['steps'].append({
            'step': '1. Verificar configuração',
            'form_id_configured': bool(form_id),
            'form_id': form_id[:20] + '...' if form_id and len(form_id) > 20 else form_id,
            'using_defaults': not (current_app.config.get('GOOGLE_FORMS_PUBLIC_ID') or current_app.config.get('GOOGLE_FORMS_VIEWFORM_URL'))
        })
        
        # Passo 2: Baixar HTML
        debug_info['steps'].append({'step': '2. Baixando HTML do Forms...'})
        try:
            html = get_public_form_html(form_id)
            debug_info['steps'][-1]['success'] = True
            debug_info['steps'][-1]['html_size'] = len(html)
            debug_info['steps'][-1]['html_preview'] = html[:300]
        except Exception as e:
            debug_info['steps'][-1]['success'] = False
            debug_info['steps'][-1]['error'] = str(e)
            debug_info['status'] = 'error'
            return jsonify(debug_info), 500
        
        # Passo 3: Extrair entry IDs
        debug_info['steps'].append({'step': '3. Extraindo entry IDs...'})
        mapping = extract_entry_ids(html)
        debug_info['steps'][-1]['success'] = True
        debug_info['steps'][-1]['mapping_count'] = len(mapping)
        debug_info['steps'][-1]['mapping'] = mapping
        
        # Passo 4: Tentar obter mapping com cache/refresh
        debug_info['steps'].append({'step': '4. Obtendo mapeamento (com cache)...'})
        try:
            full_mapping = get_or_refresh_mapping(form_id, force_refresh=False)
            debug_info['steps'][-1]['success'] = True
            debug_info['steps'][-1]['mapping_count'] = len(full_mapping)
            debug_info['steps'][-1]['mapping'] = full_mapping
        except Exception as e:
            debug_info['steps'][-1]['success'] = False
            debug_info['steps'][-1]['error'] = str(e)
            debug_info['steps'].append({'step': '5. Tentando com refresh forçado...'})
            try:
                full_mapping = get_or_refresh_mapping(form_id, force_refresh=True)
                debug_info['steps'][-1]['success'] = True
                debug_info['steps'][-1]['mapping'] = full_mapping
            except Exception as e2:
                debug_info['steps'][-1]['success'] = False
                debug_info['steps'][-1]['error'] = str(e2)
        
        debug_info['status'] = 'complete'
        return jsonify(debug_info)
        
    except Exception as e:
        debug_info['status'] = 'error'
        debug_info['error'] = str(e)
        return jsonify(debug_info), 500


@surgery.route('/surgery_requests/debug/forms-clear-cache', methods=['POST'])
@login_required
@require_admin
def debug_forms_clear_cache():
    """Limpar cache de mapeamento do Forms"""
    from pathlib import Path
    
    cache_file = Path(__file__).parent.parent.parent / 'instance' / 'forms_mapping.json'
    
    try:
        if cache_file.exists():
            cache_file.unlink()
            return jsonify({'ok': True, 'message': 'Cache limpo com sucesso'}), 200
        else:
            return jsonify({'ok': True, 'message': 'Cache não existia'}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@surgery.route('/surgery_requests/debug/forms-html', methods=['GET'])
@login_required
@require_admin
def debug_forms_html():
    """Salva o HTML completo do Forms para análise"""
    from src.services.forms_service import get_public_form_html, get_forms_configuration
    from pathlib import Path
    
    # ISSUE 1 FIX: Use new configuration resolution with defaults
    try:
        form_id, view_url = get_forms_configuration()
    except ValueError as e:
        return jsonify({
            'error': f'Forms configuration error: {str(e)}'
        }), 500
    
    try:
        html = get_public_form_html(form_id)
        
        # Salvar em arquivo
        html_file = Path(__file__).parent.parent.parent / 'instance' / 'forms_debug.html'
        html_file.parent.mkdir(exist_ok=True)
        html_file.write_text(html, encoding='utf-8')
        
        # Análise rápida
        import re
        entries = re.findall(r'entry\.(\d+)', html)
        unique_entries = sorted(set(entries))
        
        return jsonify({
            'ok': True,
            'html_size': len(html),
            'html_file': str(html_file),
            'entries_found': unique_entries,
            'entry_count': len(unique_entries),
            'message': f'HTML salvo em {html_file}'
        })
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@surgery.route('/surgery_requests/debug/forms-analysis', methods=['GET'])
@login_required
@require_admin
def debug_forms_analysis():
    """Analisa o HTML do Forms para encontrar padrões de entrada"""
    from src.services.forms_service import get_public_form_html, get_forms_configuration
    import re
    
    # ISSUE 1 FIX: Use new configuration resolution with defaults
    try:
        form_id, view_url = get_forms_configuration()
    except ValueError as e:
        return jsonify({
            'error': f'Forms configuration error: {str(e)}'
        }), 500
    
    try:
        html = get_public_form_html(form_id)
        
        analysis = {
            'form_id': form_id,
            'html_size': len(html),
            'patterns': {}
        }
        
        # Procurar por diferentes padrões de entrada
        patterns = {
            'entry_simple': r'entry\.(\d+)(?![.\d])',  # entry.123 (não seguido por . ou dígito)
            'entry_with_suffix': r'entry\.(\d+)\.(\w+)',  # entry.123.suffix
            'input_name': r'name=["\']?([^\s"\']+)["\']?',  # name="..."
            'name_entry': r'name=["\']?(entry\.\d+[^"\']*)["\']?',  # name="entry...."
        }
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, html)
            if matches:
                if isinstance(matches[0], tuple):
                    analysis['patterns'][pattern_name] = [str(m) for m in list(set(matches))[:15]]
                else:
                    analysis['patterns'][pattern_name] = list(set(matches))[:15]
        
        # Procurar por "Datas", "Descrição", "OPME", "UTI" ou variações
        field_keywords = {
            'data': r'[Dd]ata|[Dd]ate|quando',
            'descricao': r'[Dd]escri|[Dd]etail|[Oo]bserva',
            'opme': r'[OO][Pp][Mm][Ee]|material',
            'uti': r'[Uu][Tt][Ii]|intensiv',
            'procedimento': r'[Pp]roced|[Ss]urgery|[Cc]irurg',
            'ortopedista': r'[Oo]rto|[Dd]octor|[Mm]edic'
        }
        
        analysis['field_detection'] = {}
        for field, keyword_pattern in field_keywords.items():
            if re.search(keyword_pattern, html, re.IGNORECASE):
                analysis['field_detection'][field] = 'encontrado'
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
