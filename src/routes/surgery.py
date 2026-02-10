from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from src.models.surgery_request import SurgeryRequest
from src.models.patient import Patient
from src.extensions import db, csrf
from src.utils.pdf_utils import preencher_formulario_internacao, preencher_requisicao_hemocomponente
from src.forms.surgery_form import SurgeryRequestForm
from datetime import datetime
import os
import logging

surgery = Blueprint('surgery', __name__)
logger = logging.getLogger(__name__)


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
@csrf.exempt
def schedule_confirm(id):
    """
    Confirma e envia agendamento submetendo resposta ao Google Forms.
    O Apps Script da planilha (onFormSubmit) criará o evento no calendário.
    """
    from src.services.forms_service import build_forms_payload, submit_form
    
    try:
        # Buscar solicitação e paciente
        surgery_request = SurgeryRequest.query.get_or_404(id)
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
                'message': f'Configuração do Google Forms: {str(e)}'
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
            'message': f'Erro inesperado: {str(e)}'
        }), 500


@surgery.route('/surgery_requests/debug/forms-mapping', methods=['GET'])
@login_required
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
