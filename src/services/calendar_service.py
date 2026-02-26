"""
Serviço para fetch, parse e cache de eventos do Google Calendar (ICS).
"""
import logging
import requests
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from urllib.parse import quote
import pytz
from icalendar import Calendar
from dateutil import tz as dateutil_tz
from dateutil.rrule import rrulestr

logger = logging.getLogger(__name__)


class CalendarService:
    """Serviço para obter e processar eventos do Google Calendar"""
    
    def __init__(self, calendar_id: str, timezone_str: str = "America/Fortaleza", 
                 ics_url: Optional[str] = None, request_timeout: int = 10):
        """
        Inicializa o serviço de calendário.
        
        Args:
            calendar_id: ID do calendário Google (ex: s4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com)
            timezone_str: Timezone IANA (padrão: America/Fortaleza)
            ics_url: URL ICS customizada (se não fornecida, será construída)
            request_timeout: Timeout em segundos para requisições HTTP
        """
        self.calendar_id = calendar_id
        self.timezone_str = timezone_str
        self.request_timeout = request_timeout
        
        # Construir URL ICS se não fornecida
        if ics_url:
            self.ics_url = ics_url
        else:
            calendar_id_encoded = quote(calendar_id, safe="")
            self.ics_url = f"https://calendar.google.com/calendar/ical/{calendar_id_encoded}/public/basic.ics"
        
        # Timezone para conversão
        try:
            self.tz = pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Timezone desconhecido: {timezone_str}. Usando UTC.")
            self.tz = pytz.UTC
    
    def fetch_events(self) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Faz fetch do arquivo ICS e retorna eventos parseados.
        
        Returns:
            (eventos, erro)
            eventos: lista de dicts com eventos normalizados
            erro: mensagem de erro se falhar (None se sucesso)
        """
        try:
            logger.info(f"Buscando eventos do calendário: {self.calendar_id}")
            response = requests.get(self.ics_url, timeout=self.request_timeout)
            response.raise_for_status()
            
            events = self._parse_ics(response.text)
            logger.info(f"Parseado com sucesso: {len(events)} eventos")
            return events, None
        
        except requests.exceptions.Timeout:
            error = "Timeout ao buscar calendário (servidor demorou)"
            logger.error(error)
            return [], error
        
        except requests.exceptions.ConnectionError:
            error = "Erro de conexão ao buscar calendário"
            logger.error(error)
            return [], error
        
        except requests.exceptions.HTTPError as e:
            error = f"Calendário não encontrado ou sem acesso (HTTP {e.response.status_code})"
            logger.error(error)
            return [], error
        
        except Exception as e:
            error = f"Erro ao buscar calendário: {str(e)}"
            logger.error(error)
            return [], error
    
    def _parse_ics(self, ics_content: str) -> List[Dict[str, Any]]:
        """
        Parse o conteúdo ICS e retorna lista de eventos normalizados.
        """
        events = []
        
        try:
            cal = Calendar.from_ical(ics_content)
        except Exception as e:
            logger.error(f"Erro ao fazer parse ICS: {e}")
            return []
        
        # Iterar sobre componentes
        for component in cal.walk():
            if component.name == "VEVENT":
                try:
                    event = self._normalize_event(component)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.warning(f"Erro ao normalizar evento: {e}")
                    continue
        
        # Ordenar por data de início
        events.sort(key=lambda e: e["start"])
        return events
    
    def _normalize_event(self, component) -> Optional[Dict[str, Any]]:
        """
        Normaliza um componente VEVENT para dict padrão.
        
        IMPORTANTE: Para eventos all-day (VALUE=DATE), preserva a data pura
        sem conversão de timezone, evitando o deslocamento de -1 dia.
        """
        try:
            # Extrair campos
            uid = str(component.get("UID", ""))
            title = str(component.get("SUMMARY", "Sem título"))
            location = component.get("LOCATION")
            if location:
                location = str(location)
            
            description = component.get("DESCRIPTION")
            if description:
                description = str(description)
            
            # Tratar DTSTART e DTEND
            dtstart = component.get("DTSTART")
            dtend = component.get("DTEND")
            
            if not dtstart:
                return None
            
            # ========================================
            # CASO 1: All-day (VALUE=DATE)
            # ========================================
            if isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime):
                # É um date puro, não datetime
                # REGRA: Nunca converter date para datetime para all-day
                all_day = True
                start_date = dtstart.dt  # Preservar date puro
                
                # Para end_date:
                # Em ICS, DTEND para all-day é exclusive (próximo dia)
                # Exemplo: DTSTART:20260206, DTEND:20260207 = evento no dia 06
                if dtend:
                    dtend_val = dtend.dt
                    if isinstance(dtend_val, date) and not isinstance(dtend_val, datetime):
                        # DTEND é também date (exclusive)
                        end_date = dtend_val - timedelta(days=1)  # Recuar 1 dia para ficar no mesmo dia
                    else:
                        # DTEND é datetime (improvável em all-day, mas tratar)
                        end_date = dtend_val.date()
                else:
                    # Sem DTEND: evento é só de 1 dia
                    end_date = start_date
                
                # Para exibição/compatibilidade, criar datetime local "fictício" ao meio-dia
                # (não será usado para agrupamento por dia)
                start_dt = datetime.combine(start_date, datetime.min.time())
                start_dt = self.tz.localize(start_dt)  # Localize na timezone local DIRETAMENTE
                
                end_dt = datetime.combine(end_date, datetime.min.time())
                end_dt = self.tz.localize(end_dt)
                
                return {
                    "uid": uid,
                    "title": title,
                    "start": start_dt,
                    "end": end_dt,
                    "start_date": start_date,  # NOVO: date puro para all-day
                    "end_date": end_date,      # NOVO: date puro para all-day
                    "all_day": all_day,
                    "location": location,
                    "description": description,
                }
            
            # ========================================
            # CASO 2: Timed (datetime)
            # ========================================
            else:
                all_day = False
                start_dt = dtstart.dt
                
                if dtend:
                    end_dt = dtend.dt
                else:
                    # Sem DTEND: assumir duração de 30 min
                    end_dt = start_dt + timedelta(minutes=30)
                
                # Converter para timezone local se necessário
                if isinstance(start_dt, datetime) and start_dt.tzinfo is None:
                    # Naive datetime; assumir UTC
                    start_dt = pytz.UTC.localize(start_dt)
                
                if isinstance(end_dt, datetime) and end_dt.tzinfo is None:
                    end_dt = pytz.UTC.localize(end_dt)
                
                # Converter para timezone local
                if isinstance(start_dt, datetime):
                    start_dt = start_dt.astimezone(self.tz)
                    end_dt = end_dt.astimezone(self.tz)
                
                return {
                    "uid": uid,
                    "title": title,
                    "start": start_dt,
                    "end": end_dt,
                    "all_day": all_day,
                    "location": location,
                    "description": description,
                }
        
        except Exception as e:
            logger.warning(f"Erro ao normalizar evento: {e}")
            return None
    
    def filter_events(self, events: List[Dict[str, Any]], 
                      start_date: date, end_date: date, 
                      query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filtra eventos por intervalo de data e texto opcional.
        
        Args:
            events: lista de eventos
            start_date: data inicial (inclusive)
            end_date: data final (inclusive)
            query: texto para filtrar títulos (case-insensitive)
        
        Returns:
            lista de eventos filtrados
        """
        filtered = []
        
        for event in events:
            # Determinar a data do evento para comparação
            if event.get("all_day") and event.get("start_date"):
                event_date = event["start_date"]
            else:
                event_date = event["start"].date()
            
            # Filtro por data (simples: verificar se data está no intervalo)
            if event_date < start_date or event_date > end_date:
                continue
            
            # Filtro por query (título OU descrição)
            if query:
                query_lower = query.lower()
                title_match = query_lower in event["title"].lower()
                desc_match = event["description"] and query_lower in event["description"].lower()
                if not (title_match or desc_match):
                    continue
            
            filtered.append(event)
        
        return filtered
    
    def group_events_by_day(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Agrupa eventos por dia (data local no timezone).
        
        Para all-day events, usa start_date (date puro).
        Para timed events, usa start.date() (datetime convertido para date).
        
        Returns:
            {
                "YYYY-MM-DD": [eventos...],
                ...
            }
        """
        grouped = {}
        
        for event in events:
            # Extrair data do start
            # Se for all-day e temos start_date, usar; senão, usar start.date()
            if event.get("all_day") and event.get("start_date"):
                date_key = event["start_date"].isoformat()
            else:
                date_key = event["start"].date().isoformat()
            
            if date_key not in grouped:
                grouped[date_key] = []
            
            grouped[date_key].append(event)
        
        # Ordenar eventos dentro de cada dia
        for date_key in grouped:
            grouped[date_key].sort(key=lambda e: e["start"])
        
        return grouped
    
    @staticmethod
    def format_time(dt: datetime, all_day: bool = False) -> str:
        """
        Formata um datetime como HH:MM ou "Dia inteiro".
        """
        if all_day:
            return "Dia inteiro"
        
        if isinstance(dt, datetime):
            return dt.strftime("%H:%M")
        
        return str(dt)
    
    @staticmethod
    def format_date(date_obj: date) -> str:
        """
        Formata uma data como "Seg, DD/MM/YYYY".
        """
        days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        day_name = days[date_obj.weekday()]
        return f"{day_name}, {date_obj.strftime('%d/%m/%Y')}"


def get_calendar_service(app=None) -> CalendarService:
    """
    Factory para criar CalendarService a partir da config da aplicação.
    """
    from flask import current_app
    
    config = app.config if app else current_app.config
    
    calendar_id = config.get("GOOGLE_CALENDAR_ID")
    timezone_str = config.get("GOOGLE_CALENDAR_TZ", "America/Fortaleza")
    ics_url = config.get("GOOGLE_CALENDAR_ICS_URL")
    cache_ttl = config.get("CALENDAR_CACHE_TTL_MINUTES", 15)
    
    if not calendar_id:
        raise ValueError("GOOGLE_CALENDAR_ID não configurado")
    
    return CalendarService(
        calendar_id=calendar_id,
        timezone_str=timezone_str,
        ics_url=ics_url
    )
