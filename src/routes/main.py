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
        view = request.args.get('view', 'week')  # week ou month
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        query = request.args.get('q', '').strip() or None
        
        # Determinar intervalo
        today = date.today()
        
        if start_str and end_str:
            try:
                start_date = datetime.fromisoformat(start_str).date()
                end_date = datetime.fromisoformat(end_str).date()
            except:
                start_date = today
                end_date = today + timedelta(days=7)
        else:
            if view == 'month':
                # Primeiro ao último dia do mês
                first = today.replace(day=1)
                last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                start_date = first
                end_date = last
            else:  # week
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
                        events.append(evt)
                    logger.warning("Usando cache antigo por falha de fetch")
                except:
                    events = []
        
        # Filtrar por intervalo e query
        filtered_events = calendar_service.filter_events(events, start_date, end_date, query)
        
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