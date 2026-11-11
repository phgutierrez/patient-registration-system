from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from src.models.surgery_request import SurgeryRequest
from src.models.patient import Patient
from src.extensions import db, limiter
from src.pdf.snapshots import (
    create_request_snapshots, ensure_legacy_snapshot, render_snapshot,
)
from src.forms.surgery_form import SurgeryRequestForm
from src.runtime_security import (
    can_delete_surgery,
    ensure_patient_access,
    ensure_surgery_access,
    require_admin,
)
from src.services.specialty_service import (
    get_active_specialty, get_procedure_choices, get_user_choices,
    get_procedure_code_map, get_sus_code_for_procedure, get_specialty_settings,
)
from datetime import datetime
from io import BytesIO
import os
import logging
import json
import unicodedata
import re
import uuid

surgery = Blueprint('surgery', __name__)
logger = logging.getLogger(__name__)


def _normalize_text(value):
    """Normaliza texto para comparação sem acentos/case."""
    if not value:
        return ''
    text = unicodedata.normalize('NFKD', str(value))
    return ''.join(ch for ch in text if not unicodedata.combining(ch)).strip().lower()


def _confirmation_redirect(surgery_request):
    return redirect(url_for('surgery.confirmation', surgery_id=surgery_request.id))


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


def _send_authorized_pdf(surgery_request, document_type, download_name, *, as_attachment):
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error

    try:
        snapshot = ensure_legacy_snapshot(surgery_request, document_type, current_user)
        if snapshot is None:
            flash('Este documento não se aplica à solicitação.', 'warning')
            return _confirmation_redirect(surgery_request)
        pdf_bytes = render_snapshot(snapshot)
    except Exception:
        logger.exception(
            'Falha ao regenerar PDF surgery_id=%s documento=%s',
            surgery_request.id,
            document_type,
        )
        flash('Não foi possível regenerar o PDF solicitado.', 'danger')
        return _confirmation_redirect(surgery_request)

    response = send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=as_attachment,
        download_name=download_name,
        conditional=False,
        max_age=0,
    )
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Length'] = str(len(pdf_bytes))
    if not as_attachment:
        frame_policy = "frame-ancestors 'self'; object-src 'self'"
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = frame_policy
        response.headers['Content-Security-Policy-Report-Only'] = frame_policy
    return response

@surgery.route('/patient/<int:patient_id>/surgery/request', methods=['GET', 'POST'])
@login_required
def request_surgery(patient_id):
    patient = Patient.query.filter_by(id=patient_id, sync_deleted=False).first_or_404()
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

            # Persiste somente os dados versionados; os bytes são descartados após validação.
            create_request_snapshots(
                patient, surgery_request, surgery_request.created_by_user or current_user
            )
            db.session.commit()
            return redirect(url_for(
                'surgery.confirmation', surgery_id=surgery_request_id
            ))
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
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error
    patient = Patient.query.filter_by(id=surgery_request.patient_id, sync_deleted=False).first_or_404()

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
            _apply_form_to_surgery_request(surgery_request, form, specialty, sus_code, opme_value)
            db.session.flush()
            create_request_snapshots(
                patient,
                surgery_request,
                surgery_request.created_by_user or current_user,
            )
            db.session.commit()
            flash('Solicitação atualizada. Uma nova revisão dos documentos foi registrada.', 'success')
            return _confirmation_redirect(surgery_request)
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
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error
    patient = Patient.query.filter_by(id=surgery_request.patient_id, sync_deleted=False).first_or_404()

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


@surgery.route('/surgery/<int:surgery_id>/delete', methods=['POST'])
@login_required
def delete_surgery_request(surgery_id):
    """Exclui uma solicitação (autor ou admin). Com sync ativa vira tombstone."""
    from src.models.calendar_event_status import CalendarEventStatus

    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error
    if not can_delete_surgery(surgery_request):
        flash('Somente quem criou a solicitação ou um administrador pode excluí-la.', 'danger')
        return _confirmation_redirect(surgery_request)

    patient_id = surgery_request.patient_id
    was_scheduled = (surgery_request.calendar_status or '').lower() == 'agendado'
    label = surgery_request.procedimento_solicitado or f'#{surgery_request.id}'
    try:
        for status in CalendarEventStatus.query.filter_by(surgery_request_id=surgery_request.id).all():
            status.surgery_request_id = None
        db.session.delete(surgery_request)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('Falha ao excluir surgery_id=%s', surgery_id)
        flash('Não foi possível excluir a solicitação.', 'danger')
        return redirect(url_for('patients.view_patient', id=patient_id))

    if was_scheduled:
        flash(
            f'Solicitação "{label}" excluída. Ela já estava na agenda: remova o evento '
            'manualmente no Google Agenda.',
            'warning',
        )
    else:
        flash(f'Solicitação "{label}" excluída com sucesso.', 'success')
    next_url = request.form.get('next', '')
    if next_url.startswith('/') and not next_url.startswith('//'):
        return redirect(next_url)
    return redirect(url_for('patients.view_patient', id=patient_id))


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
        
        snapshot = ensure_legacy_snapshot(surgery_request, 'internacao')
        pdf_bytes = render_snapshot(snapshot)

        return f"""
        <h2>Teste de Geração de PDF</h2>
        <p><strong>Status:</strong> PDF regenerado em memória com sucesso.</p>
        <p><strong>Tamanho:</strong> {len(pdf_bytes)} bytes</p>
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
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    return _send_authorized_pdf(
        surgery_request,
        'internacao',
        f"Internacao_{surgery_request.patient_id}.pdf",
        as_attachment=True,
    )

@surgery.route('/surgery/<int:surgery_id>/pdf/<path:pdf_name>')
@login_required
def download_pdf_legacy(surgery_id, pdf_name):
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    if surgery_request.pdf_filename != os.path.basename(pdf_name):
        flash('O arquivo PDF solicitado não corresponde à solicitação.', 'danger')
        return redirect(url_for('patients.view_patient', id=surgery_request.patient_id))
    return redirect(url_for('surgery.download_pdf', surgery_id=surgery_id))


@surgery.route('/surgery/<int:surgery_id>/pdf/view')
@login_required
@limiter.limit('30 per hour')
def view_pdf(surgery_id):
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    return _send_authorized_pdf(
        surgery_request,
        'internacao',
        f"Internacao_{surgery_request.patient_id}.pdf",
        as_attachment=False,
    )


@surgery.route('/surgery/<int:surgery_id>/pdf-hemocomponente')
@login_required
@limiter.limit('20 per hour')
def download_pdf_hemocomponente(surgery_id):
    """Rota para download do PDF de requisição de hemocomponente"""
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    access_error = ensure_surgery_access(surgery_request)
    if access_error:
        return access_error

    if not surgery_request.reserva_sangue:
        flash('Nenhuma reserva de sangue foi solicitada para esta cirurgia.', 'warning')
        return _confirmation_redirect(surgery_request)

    return _send_authorized_pdf(
        surgery_request,
        'hemocomponente',
        f"Requisicao_Hemocomponente_{surgery_request.patient_id}.pdf",
        as_attachment=True,
    )


@surgery.route('/surgery/<int:surgery_id>/pdf-hemocomponente/<path:pdf_name>')
@login_required
def download_pdf_hemocomponente_legacy(surgery_id, pdf_name):
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    if surgery_request.pdf_hemocomponente != os.path.basename(pdf_name):
        flash('O arquivo PDF solicitado não corresponde à solicitação.', 'danger')
        return _confirmation_redirect(surgery_request)
    return redirect(url_for('surgery.download_pdf_hemocomponente', surgery_id=surgery_id))


@surgery.route('/surgery/<int:surgery_id>/pdf-hemocomponente/view')
@login_required
@limiter.limit('20 per hour')
def view_pdf_hemocomponente(surgery_id):
    surgery_request = SurgeryRequest.query.filter_by(id=surgery_id, sync_deleted=False).first_or_404()
    if not surgery_request.reserva_sangue:
        flash('Nenhuma reserva de sangue foi solicitada para esta cirurgia.', 'warning')
        return _confirmation_redirect(surgery_request)
    return _send_authorized_pdf(
        surgery_request,
        'hemocomponente',
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
    from src.services.forms_service import (
        build_forms_payload, OPME_FORM_CHOICES, ORTHOPEDIST_CHOICES,
    )
    
    try:
        # Buscar solicitação e paciente
        surgery_request = SurgeryRequest.query.filter_by(id=id, sync_deleted=False).first_or_404()
        access_error = ensure_surgery_access(surgery_request)
        if access_error:
            return access_error
        patient = Patient.query.filter_by(id=surgery_request.patient_id, sync_deleted=False).first_or_404()
        
        # Verificar se já foi agendado
        already_scheduled = surgery_request.calendar_status == 'agendado'
        
        # Montar payload do Forms
        try:
            payload = build_forms_payload(surgery_request, patient)
            
            # Formatar preview para exibição
            preview = {
                'title': payload['procedure_title'],
                'procedure_title': payload['procedure_title'],
                'date': payload['date'],
                'date_display': payload['date'],
                'orthopedist': payload['orthopedist'],
                'needs_icu': payload['needs_icu'],
                'needs_icu_display': payload['needs_icu'],
                'opme': payload['opme'],
                'opme_other': payload.get('opme_other', ''),
                'opme_display': ', '.join(payload['opme']) if payload['opme'] else 'Não',
                'full_description': payload['full_description'],
                'description': payload['full_description'],
                'all_day': True,
                'opme_choices': OPME_FORM_CHOICES,
                'orthopedist_choices': ORTHOPEDIST_CHOICES,
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
    from src.services.forms_service import (
        build_forms_payload, submit_form, get_forms_configuration,
        validate_schedule_payload,
    )
    
    try:
        # Buscar solicitação e paciente
        surgery_request = SurgeryRequest.query.filter_by(id=id, sync_deleted=False).first_or_404()
        access_error = ensure_surgery_access(surgery_request)
        if access_error:
            return access_error
        patient = Patient.query.filter_by(id=surgery_request.patient_id, sync_deleted=False).first_or_404()
        request_payload = request.get_json(silent=True) or {}

        from src.sync import sync_service
        runtime = sync_service.runtime
        if runtime and runtime.ready:
            try:
                sync_service.sync_once()
                db.session.refresh(surgery_request)
            except Exception:
                logger.warning(
                    'Sincronização prévia indisponível para surgery_id=%s', id
                )

        if surgery_request.scheduled_result_uncertain:
            return jsonify({
                'ok': False,
                'code': 'EXTERNAL_RESULT_UNCERTAIN',
                'message': (
                    'Uma tentativa anterior ficou com resultado incerto. '
                    'Verifique o Google Forms antes de tentar novamente.'
                ),
                'attempt_id': surgery_request.scheduled_attempt_id,
            }), 409

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
            defaults = build_forms_payload(surgery_request, patient)
            payload = validate_schedule_payload(request_payload, defaults)
            reference = f'[SOLICITACAO:{surgery_request.sync_uuid}]'
            if reference not in payload['full_description']:
                referenced_description = (
                    payload['full_description'].rstrip() + '\n\n' + reference
                )
                if len(referenced_description) > 5000:
                    raise ValueError(
                        'Descrição muito longa para incluir a referência interna da solicitação.'
                    )
                payload['full_description'] = referenced_description
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

        coordination = None
        attempt_id = str(uuid.uuid4())
        if runtime and runtime.enabled:
            from src.services.external_coordination import acquire_forms_lock
            coordination = acquire_forms_lock(surgery_request.sync_uuid)
            attempt_id = coordination.attempt_uuid
            if not coordination.available and not request_payload.get(
                'allow_offline_duplicate_risk', False
            ):
                return jsonify({
                    'ok': False,
                    'code': 'SYNC_OFFLINE_CONFIRMATION_REQUIRED',
                    'requires_offline_confirmation': True,
                    'message': (
                        'A pasta de sincronização está indisponível. O envio '
                        'pode ser duplicado por outra estação. Confirme para continuar.'
                    ),
                }), 409
            if coordination.available and not coordination.acquired:
                return jsonify({
                    'ok': False,
                    'code': 'EXTERNAL_ATTEMPT_IN_PROGRESS',
                    'message': coordination.message,
                }), 409

        surgery_request.scheduled_attempt_id = attempt_id
        surgery_request.scheduled_result_uncertain = True
        surgery_request.calendar_status = 'enviando'
        db.session.commit()
        sync_service.wake()

        try:
            success, message, status_code = submit_form(
                form_public_id, payload, timeout
            )
        finally:
            if coordination is not None:
                coordination.release()

        if success:
            # Atualizar registro com dados do agendamento
            surgery_request.calendar_status = 'agendado'
            surgery_request.scheduled_at = datetime.utcnow()
            
            # Não temos event_id/link direto (será criado pelo Apps Script da planilha)
            # Mas podemos adicionar link para o Forms ou deixar None
            surgery_request.scheduled_event_link = None  # Será criado pelo Apps Script
            surgery_request.scheduled_result_uncertain = False
            
            db.session.commit()
            
            logger.info(f"Cirurgia {id} enviada ao Google Forms com sucesso")
            
            return jsonify({
                'ok': True,
                'message': 'Agendamento enviado com sucesso! O evento será criado automaticamente no Google Calendar.',
                'scheduledAt': surgery_request.scheduled_at.isoformat(),
                'attempt_id': attempt_id
            })
        else:
            # Salvar status de erro
            surgery_request.scheduled_result_uncertain = status_code in (500, 502, 504)
            surgery_request.calendar_status = (
                'incerto' if surgery_request.scheduled_result_uncertain else 'erro'
            )
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
