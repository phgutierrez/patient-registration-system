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
            
            # Verificar se é all-day (date vs datetime)
            all_day = False
            if isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime):
                # É um date, não datetime
                all_day = True
                start_dt = datetime.combine(dtstart.dt, datetime.min.time())
                # Se DTEND existe, usar; senão, usar start
                if dtend:
                    if isinstance(dtend.dt, date) and not isinstance(dtend.dt, datetime):
                        end_dt = datetime.combine(dtend.dt, datetime.min.time())
                    else:
                        end_dt = dtend.dt
                else:
                    end_dt = start_dt + timedelta(days=1)
            else:
                # É um datetime
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
        
        # Converter datas para datetime (início e fim do dia no timezone local)
        start_dt = datetime.combine(start_date, datetime.min.time())
        start_dt = self.tz.localize(start_dt)
        
        end_dt = datetime.combine(end_date, datetime.max.time())
        end_dt = self.tz.localize(end_dt)
        
        for event in events:
            # Filtro por data
            event_start = event["start"]
            event_end = event["end"]
            
            # Verificar se o evento está no intervalo
            # (overlaps: event.start < end_dt AND event.end > start_dt)
            if event_start >= end_dt or event_end <= start_dt:
                continue
            
            # Filtro por query (título)
            if query:
                if query.lower() not in event["title"].lower():
                    continue
            
            filtered.append(event)
        
        return filtered
    
    def group_events_by_day(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Agrupa eventos por dia (data local no timezone).
        
        Returns:
            {
                "YYYY-MM-DD": [eventos...],
                ...
            }
        """
        grouped = {}
        
        for event in events:
            # Extrair data do start
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
