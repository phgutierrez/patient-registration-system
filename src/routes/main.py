from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import os
import sys
import threading
import logging
from datetime import datetime, date, timedelta
import json

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

# Variável para rastrear última atividade
last_activity = None

@main.route('/')
@main.route('/index')
@login_required
def index():
    return render_template('index.html')

@main.route('/api/heartbeat', methods=['GET'])
@login_required
def heartbeat():
    """Rota para receber heartbeat do cliente e manter a conexão viva"""
    global last_activity
    from datetime import datetime
    last_activity = datetime.now()
    return jsonify({'status': 'alive', 'timestamp': last_activity.isoformat()}), 200

@main.route('/api/browser-closing', methods=['POST'])
@login_required
def browser_closing():
    """Rota notificada quando o navegador está sendo fechado"""
    logger.info('Navegador/aba sendo fechado. Encerrando aplicação...')
    
    def shutdown_server():
        """Função para encerrar o servidor"""
        import time
        time.sleep(1)
        try:
            sys.exit(0)
        except:
            os._exit(0)
    
    # Iniciar thread de shutdown
    threading.Thread(target=shutdown_server, daemon=True).start()
    
    return jsonify({'success': True}), 200

@main.route('/shutdown', methods=['POST'])
@login_required
def shutdown():
    """Rota para desligar o servidor"""
    try:
        def shutdown_server():
            """Função para encerrar o servidor após responder à requisição"""
            import time
            time.sleep(1)  # Aguardar a resposta ser enviada
            
            # Tentar diferentes métodos de shutdown
            try:
                # Método 1: Usar sys.exit() em uma thread separada
                sys.exit(0)
            except:
                # Método 2: Forçar encerramento do processo
                os._exit(0)
        
        # Iniciar thread de shutdown
        threading.Thread(target=shutdown_server, daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Servidor sendo encerrado...'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/agenda')
def agenda():
    """Exibe a agenda cirúrgica a partir do Google Calendar (ICS)"""
    from src.services.calendar_service import get_calendar_service
    from src.extensions import db
    from src.models import CalendarCache
    from flask import current_app
    
    try:
        # Parâmetros de query
        view = request.args.get('view', 'month')  # week ou month (padrão: month)
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        query = request.args.get('q', '').strip() or None
        month_str = request.args.get('month')  # formato: YYYY-MM
        
        # Determinar intervalo
        today = date.today()
        
        # Se modo month, SEMPRE usar mês completo (ignorar start/end da semana anterior)
        if view == 'month':
            if month_str:
                try:
                    year, month = map(int, month_str.split('-'))
                    first = date(year, month, 1)
                    last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    start_date = first
                    end_date = last
                except:
                    first = today.replace(day=1)
                    last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    start_date = first
                    end_date = last
            else:
                # Usar mês atual
                first = today.replace(day=1)
                last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                start_date = first
                end_date = last
        # Modo semana (week)
        elif start_str and end_str:
            try:
                start_date = datetime.fromisoformat(start_str).date()
                end_date = datetime.fromisoformat(end_str).date()
            except:
                start_date = today
                end_date = today + timedelta(days=7)
        else:
            # Padrão: semana atual
            start_date = today
            end_date = today + timedelta(days=7)
        
        # Obter serviço
        calendar_service = get_calendar_service(current_app)
        
        # Verificar cache
        cache = CalendarCache.query.filter_by(calendar_id=calendar_service.calendar_id).first()
        cache_valid = False
        use_stale = False
        cache_ttl_minutes = current_app.config.get('CALENDAR_CACHE_TTL_MINUTES', 15)
        
        if cache and cache.fetched_at:
            age_minutes = (datetime.utcnow() - cache.fetched_at).total_seconds() / 60
            cache_valid = age_minutes < cache_ttl_minutes
        
        # Fetch eventos
        events = []
        error = None
        meta_source = "none"
        
        if cache_valid and cache and cache.events_json:
            # Usar cache válido
            try:
                events_data = json.loads(cache.events_json)
                # Reconverter datas de ISO string para datetime
                events = []
                for evt in events_data:
                    evt['start'] = datetime.fromisoformat(evt['start'])
                    evt['end'] = datetime.fromisoformat(evt['end'])
                    # Converter datas de all-day se existirem
                    if evt.get('start_date'):
                        evt['start_date'] = datetime.fromisoformat(evt['start_date']).date()
                    if evt.get('end_date'):
                        evt['end_date'] = datetime.fromisoformat(evt['end_date']).date()
                    events.append(evt)
                meta_source = "cache"
                logger.info("Usando cache válido para calendário")
            except Exception as e:
                logger.warning(f"Erro ao desserializar cache: {e}")
                cache_valid = False
        
        if not cache_valid:
            # Fazer fetch
            logger.info("Buscando eventos do calendário...")
            events, error = calendar_service.fetch_events()
            
            if events:
                meta_source = "live"
                # Atualizar cache
                events_json = json.dumps(
                    [
                        {
                            'uid': e['uid'],
                            'title': e['title'],
                            'start': e['start'].isoformat(),
                            'end': e['end'].isoformat(),
                            'start_date': e.get('start_date').isoformat() if e.get('start_date') else None,
                            'end_date': e.get('end_date').isoformat() if e.get('end_date') else None,
                            'all_day': e['all_day'],
                            'location': e['location'],
                            'description': e['description'],
                        }
                        for e in events
                    ]
                )
                
                if not cache:
                    cache = CalendarCache(calendar_id=calendar_service.calendar_id)
                    db.session.add(cache)
                
                cache.fetched_at = datetime.utcnow()
                cache.events_json = events_json
                cache.error_message = None
                db.session.commit()
                logger.info("Cache atualizado")
            
            elif cache and cache.events_json:
                # Falhou; usar cache antigo
                meta_source = "stale_cache"
                try:
                    events_data = json.loads(cache.events_json)
                    events = []
                    for evt in events_data:
                        evt['start'] = datetime.fromisoformat(evt['start'])
                        evt['end'] = datetime.fromisoformat(evt['end'])
                        # Converter datas de all-day se existirem
                        if evt.get('start_date'):
                            evt['start_date'] = datetime.fromisoformat(evt['start_date']).date()
                        if evt.get('end_date'):
                            evt['end_date'] = datetime.fromisoformat(evt['end_date']).date()
                        events.append(evt)
                    logger.warning("Usando cache antigo por falha de fetch")
                except:
                    events = []
        
        # Filtrar por intervalo e query
        filtered_events = calendar_service.filter_events(events, start_date, end_date, query)
        
        # Carregar status dos eventos do banco
        from src.models import CalendarEventStatus
        status_map = {}
        for evt_status in CalendarEventStatus.query.all():
            status_map[evt_status.event_uid] = {
                'status': evt_status.status,
                'reason': evt_status.suspension_reason
            }
        
        # Anexar status aos eventos
        for event in filtered_events:
            event_uid = event.get('uid', '')
            if event_uid in status_map:
                event['status'] = status_map[event_uid]['status']
                event['suspension_reason'] = status_map[event_uid]['reason']
            else:
                event['status'] = None
                event['suspension_reason'] = None
        
        # Agrupar por dia
        grouped = calendar_service.group_events_by_day(filtered_events)
        
        # Ordenar datas e formatar
        sorted_dates = sorted(grouped.keys())
        formatted_dates = {
            date_key: calendar_service.format_date(
                datetime.fromisoformat(date_key).date()
            )
            for date_key in sorted_dates
        }
        
        # Se modo calendário (month), gerar estrutura de semanas (weeks) para o grid
        weeks = []
        month_name = ""
        year = ""
        current_month = ""
        
        if view == 'month':
            import calendar as cal_module
            
            # Nomes dos meses em português
            month_names = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]
            
            month_name = month_names[start_date.month - 1]
            year = start_date.year
            current_month = f"{year}-{start_date.month:02d}"
            
            # Primeiro dia do mês e dia da semana
            # Python weekday(): 0=SEG, 1=TER, ..., 6=DOM
            # Nosso índice:    0=DOM, 1=SEG, ..., 6=SÁB
            first_day = start_date
            python_weekday = first_day.weekday()  # 0-6, onde 0=SEG, 6=DOM
            first_weekday = (python_weekday + 1) % 7  # Converte para: 0=DOM, 1=SEG, ..., 6=SÁB
            
            # Último dia do mês
            last_day = end_date
            last_day_of_month = cal_module.monthrange(year, start_date.month)[1]
            
            # Construir lista de cells (células individuais)
            cells = []
            
            # 1. Adicionar células vazias ANTES do primeiro dia do mês
            for _ in range(first_weekday):
                cells.append({
                    'date': None,
                    'day': None,
                    'events': [],
                    'is_other_month': True,
                    'is_today': False
                })
            
            # 2. Adicionar dias do mês
            for day_num in range(1, last_day_of_month + 1):
                current_date = date(year, start_date.month, day_num)
                day_str = current_date.isoformat()
                day_events = grouped.get(day_str, [])
                
                cells.append({
                    'date': current_date,
                    'day': day_num,
                    'events': day_events,
                    'is_other_month': False,
                    'is_today': current_date == today
                })
            
            # 3. Adicionar células vazias DEPOIS do último dia (para completar a última semana)
            while len(cells) % 7 != 0:
                cells.append({
                    'date': None,
                    'day': None,
                    'events': [],
                    'is_other_month': True,
                    'is_today': False
                })
            
            # 4. Agrupar células em semanas (7 por semana)
            for i in range(0, len(cells), 7):
                weeks.append(cells[i:i+7])
        
        # Contexto para template
        context = {
            'view': view,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'query': query or '',
            'grouped_events': grouped,
            'sorted_dates': sorted_dates,
            'formatted_dates': formatted_dates,
            'meta_source': meta_source,
            'error': error,
            'total_events': len(filtered_events),
            'weeks': weeks,  # Estrutura de semanas para o grid mensal
            'month_name': month_name,
            'year': year,
            'current_month': current_month,
        }
        
        return render_template('agenda.html', **context)
    
    except Exception as e:
        logger.error(f"Erro ao exibir agenda: {e}", exc_info=True)
        return render_template('agenda.html', 
                               error=f"Erro ao carregar agenda: {str(e)}",
                               view='week',
                               start_date=date.today().isoformat(),
                               end_date=(date.today() + timedelta(days=7)).isoformat(),
                               grouped_events={},
                               sorted_dates=[],
                               meta_source='none',
                               total_events=0), 500


@main.route('/agenda/events/status', methods=['POST'])
def update_event_status():
    """Atualiza o status de um evento (Realizada/Suspensa)"""
    from src.extensions import db
    from src.models import CalendarEventStatus
    
    try:
        data = request.get_json()
        
        # Validações
        if not data or 'event_uid' not in data:
            return jsonify({'ok': False, 'error': 'event_uid é obrigatório'}), 400
        
        if 'status' not in data:
            return jsonify({'ok': False, 'error': 'status é obrigatório'}), 400
        
        event_uid = data.get('event_uid', '').strip()
        status = data.get('status', '').upper()
        reason = data.get('reason', '').strip() if data.get('reason') else None
        event_date = data.get('event_date')  # Opcional: YYYY-MM-DD
        
        # Validar status
        if status not in ['REALIZADA', 'SUSPENSA']:
            return jsonify({'ok': False, 'error': 'status deve ser REALIZADA ou SUSPENSA'}), 400
        
        # Se suspensa, validar motivo
        if status == 'SUSPENSA':
            if not reason or len(reason.strip()) < 5:
                return jsonify({
                    'ok': False, 
                    'error': 'Motivo da suspensão é obrigatório (mínimo 5 caracteres)'
                }), 400
        
        # Converter event_date se fornecida
        event_date_obj = None
        if event_date:
            try:
                event_date_obj = datetime.fromisoformat(event_date).date()
            except:
                pass
        
        # Buscar ou criar registro
        event_status = CalendarEventStatus.query.filter_by(event_uid=event_uid).first()
        
        if event_status:
            # Atualizar
            event_status.status = status
            event_status.suspension_reason = reason if status == 'SUSPENSA' else None
            event_status.updated_at = datetime.utcnow()
            if event_date_obj:
                event_status.event_date = event_date_obj
        else:
            # Criar novo
            event_status = CalendarEventStatus(
                event_uid=event_uid,
                status=status,
                suspension_reason=reason if status == 'SUSPENSA' else None,
                event_date=event_date_obj
            )
            db.session.add(event_status)
        
        db.session.commit()
        
        logger.info(f"Evento {event_uid[:20]}... marcado como {status}")
        
        return jsonify({
            'ok': True,
            'status': status,
            'reason': reason if status == 'SUSPENSA' else None
        }), 200
    
    except Exception as e:
        logger.error(f"Erro ao atualizar status do evento: {e}", exc_info=True)
        return jsonify({'ok': False, 'error': f'Erro ao atualizar status: {str(e)}'}), 500
