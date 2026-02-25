"""
Serviço para agendamento automático no Google Calendar
Responsável por montar payloads e enviar eventos via Apps Script Web App
"""
from datetime import datetime
from typing import Dict, Optional, Tuple
import pytz
import logging

logger = logging.getLogger(__name__)


def build_calendar_payload(surgery_request, patient) -> Dict:
    """
    Monta o payload completo para enviar ao Apps Script Web App
    
    Args:
        surgery_request: Objeto SurgeryRequest com dados da cirurgia
        patient: Objeto Patient com dados do paciente
        
    Returns:
        dict: Payload formatado para o Apps Script
    """
    from flask import current_app
    
    # Validações básicas
    if not surgery_request.procedimento_solicitado:
        raise ValueError("Procedimento solicitado é obrigatório")
    if not surgery_request.data_cirurgia:
        raise ValueError("Data da cirurgia é obrigatória")
    
    # Obter configurações
    calendar_id = current_app.config.get('GOOGLE_CALENDAR_ID')
    timezone = current_app.config.get('GOOGLE_CALENDAR_TZ', 'America/Fortaleza')
    
    # Formatar data no formato YYYY-MM-DD
    date_str = surgery_request.data_cirurgia.strftime('%Y-%m-%d')
    
    # Montar descrição completa (igual ao que vai pro Forms)
    description_parts = []
    
    # Dados do paciente
    description_parts.append(f"📋 DADOS DO PACIENTE")
    description_parts.append(f"Nome: {patient.nome}")
    description_parts.append(f"Data de nascimento: {patient.data_nascimento.strftime('%d/%m/%Y')}")
    description_parts.append(f"Diagnóstico: {patient.diagnostico}")
    description_parts.append(f"Nº Prontuário: {patient.prontuario}")
    description_parts.append(f"Contato: {patient.contato}")
    description_parts.append("")
    
    # Dados da cirurgia
    description_parts.append(f"🏥 DADOS DA CIRURGIA")
    description_parts.append(f"Procedimento: {surgery_request.procedimento_solicitado}")
    description_parts.append(f"Data: {surgery_request.data_cirurgia.strftime('%d/%m/%Y')}")
    description_parts.append(f"Tipo: {surgery_request.tipo_cirurgia}")
    
    if surgery_request.duracao_prevista:
        description_parts.append(f"Duração prevista: {surgery_request.duracao_prevista}")
    
    description_parts.append("")
    
    # Informações clínicas
    description_parts.append(f"📝 INFORMAÇÕES CLÍNICAS")
    if surgery_request.condicoes_justificativa:
        description_parts.append(f"Condições/Justificativa: {surgery_request.condicoes_justificativa}")
    if surgery_request.sinais_sintomas:
        description_parts.append(f"Sinais e sintomas: {surgery_request.sinais_sintomas}")
    if surgery_request.resultados_diagnosticos:
        description_parts.append(f"Resultados de exames: {surgery_request.resultados_diagnosticos}")
    
    description_parts.append("")
    
    # Recursos necessários
    description_parts.append(f"🔧 RECURSOS NECESSÁRIOS")
    if surgery_request.opme:
        description_parts.append(f"OPME: {surgery_request.opme}")
    if surgery_request.aparelhos_especiais:
        description_parts.append(f"Aparelhos especiais: {surgery_request.aparelhos_especiais}")
    if surgery_request.reserva_sangue:
        qtd = surgery_request.quantidade_sangue or "não especificada"
        description_parts.append(f"Reserva de sangue: Sim ({qtd})")
    if surgery_request.reserva_uti:
        description_parts.append(f"Reserva de UTI: Sim")
    
    description = "\n".join(description_parts)
    
    # Determinar ortopedista (assistente)
    orthopedist = surgery_request.assistente or "Não especificado"
    
    # Processar OPME (string com itens separados por vírgula)
    opme_list = []
    opme_other = ""
    if surgery_request.opme:
        for part in [p.strip() for p in surgery_request.opme.split(',') if p.strip()]:
            if part.lower().startswith('outro:'):
                opme_other = part[6:].strip()
            else:
                opme_list.append(part)
    
    # Montar payload
    payload = {
        "calendarId": calendar_id,
        "title": surgery_request.procedimento_solicitado,
        "date": date_str,
        "description": description,
        "orthopedist": orthopedist,
        "opme": opme_list,
        "opme_other": opme_other,
        "needs_icu": surgery_request.reserva_uti or False
    }
    
    logger.info(f"Payload montado para surgery_request_id={surgery_request.id}")
    return payload


def build_calendar_preview(payload: Dict) -> Dict:
    """
    Monta visualização formatada do payload para exibição na UI
    
    Args:
        payload: Payload retornado por build_calendar_payload()
        
    Returns:
        dict: Dados formatados para preview
    """
    from datetime import datetime as dt
    import locale
    
    # Tentar configurar locale para PT-BR
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
        except:
            pass  # Fallback: usar inglês
    
    # Converter data para objeto date
    date_obj = dt.strptime(payload['date'], '%Y-%m-%d').date()
    
    # Formatar data com dia da semana
    try:
        # Dias da semana em português
        weekdays = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        weekday = weekdays[date_obj.weekday()]
        date_display = f"{date_obj.strftime('%d/%m/%Y')} ({weekday})"
    except:
        date_display = date_obj.strftime('%d/%m/%Y')
    
    # Formatar OPME
    opme_display = "—"
    if payload.get('opme') and len(payload['opme']) > 0:
        opme_display = ", ".join(payload['opme'])
        if payload.get('opme_other'):
            opme_display += f", {payload['opme_other']}"
    elif payload.get('opme_other'):
        opme_display = payload['opme_other']
    
    # Formatar UTI
    needs_icu_display = "Sim" if payload.get('needs_icu') else "Não"
    
    preview = {
        "title": payload['title'],
        "date_display": date_display,
        "all_day": True,
        "orthopedist": payload.get('orthopedist', '—'),
        "needs_icu_display": needs_icu_display,
        "opme_display": opme_display,
        "description": payload['description']
    }
    
    return preview


def send_to_calendar(payload: Dict, apps_script_url: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Envia payload ao Apps Script Web App para criar evento
    
    Args:
        payload: Payload montado por build_calendar_payload()
        apps_script_url: URL do endpoint do Apps Script
        
    Returns:
        tuple: (sucesso: bool, resposta: dict ou None, erro: str ou None)
    """
    import requests
    
    try:
        logger.info(f"Enviando agendamento para {apps_script_url}")
        logger.debug(f"Payload: {payload}")
        
        response = requests.post(
            apps_script_url,
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        response.raise_for_status()
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"Agendamento criado com sucesso: event_id={result.get('eventId')}")
            return True, result, None
        else:
            error_msg = result.get('error', 'Erro desconhecido do Apps Script')
            logger.error(f"Apps Script retornou erro: {error_msg}")
            return False, result, error_msg
            
    except requests.exceptions.Timeout:
        error_msg = "Tempo limite excedido ao conectar com o Google Calendar"
        logger.error(error_msg)
        return False, None, error_msg
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Erro de conexão com o Apps Script: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg
        
    except Exception as e:
        error_msg = f"Erro inesperado ao agendar: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, None, error_msg
