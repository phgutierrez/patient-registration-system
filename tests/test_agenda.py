"""
Testes para o serviço de calendário e rota /agenda
"""
import pytest
from datetime import datetime, date, timedelta
from src.services.calendar_service import CalendarService


class TestCalendarServiceParser:
    """Testes do parser ICS"""
    
    @pytest.fixture
    def ics_content_simple(self):
        """ICS simples com um evento"""
        return """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:test-event-1@example.com
DTSTART:20260205T100000Z
DTEND:20260205T110000Z
SUMMARY:Cirurgia de Escoliose
LOCATION:Sala 1
DESCRIPTION:Procedimento de fusão vertebral
END:VEVENT
END:VCALENDAR
"""
    
    @pytest.fixture
    def ics_content_allday(self):
        """ICS com evento all-day"""
        return """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-allday-1@example.com
DTSTART;VALUE=DATE:20260210
DTEND;VALUE=DATE:20260211
SUMMARY:Dia sem cirurgias
END:VEVENT
END:VCALENDAR
"""
    
    def test_parse_simple_event(self, ics_content_simple):
        """Testa parse de evento simples"""
        service = CalendarService(
            calendar_id="test@example.com",
            timezone_str="America/Fortaleza"
        )
        
        events, _ = service._parse_ics(ics_content_simple), None
        
        assert len(events) >= 1
        event = events[0]
        assert event['title'] == "Cirurgia de Escoliose"
        assert event['location'] == "Sala 1"
        assert "fusão vertebral" in event['description']
        assert event['all_day'] == False
        assert event['start'] is not None
        assert event['end'] is not None
    
    def test_parse_allday_event(self, ics_content_allday):
        """Testa parse de evento all-day"""
        service = CalendarService(
            calendar_id="test@example.com",
            timezone_str="America/Fortaleza"
        )
        
        events = service._parse_ics(ics_content_allday)
        
        assert len(events) >= 1
        event = events[0]
        assert event['all_day'] == True
        assert event['title'] == "Dia sem cirurgias"
    
    def test_filter_by_date_range(self, ics_content_simple):
        """Testa filtro por intervalo de datas"""
        service = CalendarService(
            calendar_id="test@example.com",
            timezone_str="America/Fortaleza"
        )
        
        events = service._parse_ics(ics_content_simple)
        
        # Filtro que inclui o evento (05/02/2026)
        filtered = service.filter_events(
            events,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 10),
            query=None
        )
        assert len(filtered) == 1
        
        # Filtro que exclui o evento
        filtered = service.filter_events(
            events,
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 20),
            query=None
        )
        assert len(filtered) == 0
    
    def test_filter_by_query(self, ics_content_simple):
        """Testa filtro por texto"""
        service = CalendarService(
            calendar_id="test@example.com",
            timezone_str="America/Fortaleza"
        )
        
        events = service._parse_ics(ics_content_simple)
        
        # Busca que encontra
        filtered = service.filter_events(
            events,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 10),
            query="Escoliose"
        )
        assert len(filtered) == 1
        
        # Busca que não encontra
        filtered = service.filter_events(
            events,
            start_date=date(2026, 2, 1),
            end_date=date(2026, 2, 10),
            query="Joelho"
        )
        assert len(filtered) == 0
    
    def test_group_by_day(self, ics_content_simple):
        """Testa agrupamento por dia"""
        service = CalendarService(
            calendar_id="test@example.com",
            timezone_str="America/Fortaleza"
        )
        
        events = service._parse_ics(ics_content_simple)
        grouped = service.group_events_by_day(events)
        
        assert len(grouped) >= 1
        # Deve ter uma chave ISO para cada dia com eventos


class TestAgendaRoute:
    """Testes da rota /agenda"""
    
    def test_agenda_route_returns_200(self, client):
        """Testa se a rota /agenda retorna 200 OK"""
        response = client.get('/agenda')
        assert response.status_code == 200
    
    def test_agenda_route_contains_header(self, client):
        """Testa se a página contém header 'Agenda Cirúrgica'"""
        response = client.get('/agenda')
        assert b'Agenda Cirurgica' in response.data or b'Agenda' in response.data
    
    def test_agenda_route_with_week_view(self, client):
        """Testa rota com view=week"""
        response = client.get('/agenda?view=week')
        assert response.status_code == 200
    
    def test_agenda_route_with_month_view(self, client):
        """Testa rota com view=month"""
        response = client.get('/agenda?view=month')
        assert response.status_code == 200
    
    def test_agenda_route_with_date_range(self, client):
        """Testa rota com intervalo de datas"""
        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=7)).isoformat()
        
        response = client.get(f'/agenda?start={today}&end={tomorrow}')
        assert response.status_code == 200
    
    def test_agenda_route_with_search_query(self, client):
        """Testa rota com query de busca"""
        response = client.get('/agenda?q=Escoliose')
        assert response.status_code == 200


@pytest.fixture
def client():
    """Fixture para cliente Flask de teste"""
    from src.app import app
    app.config['TESTING'] = True
    app.config['GOOGLE_CALENDAR_ID'] = 'test@example.com'
    
    with app.test_client() as client:
        with app.app_context():
            yield client
