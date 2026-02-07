"""
Testes para o sistema de agendamento automático no Google Calendar
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, time, datetime
from src.services.calendar_scheduler import (
    build_calendar_payload,
    build_calendar_preview,
    send_to_calendar
)


class MockPatient:
    """Mock de Patient para testes"""
    def __init__(self):
        self.id = 1
        self.nome = "João da Silva"
        self.data_nascimento = date(1990, 5, 15)
        self.diagnostico = "Escoliose idiopática"
        self.prontuario = "P12345"
        self.contato = "(85) 98765-4321"


class MockSurgeryRequest:
    """Mock de SurgeryRequest para testes"""
    def __init__(self):
        self.id = 10
        self.patient_id = 1
        self.procedimento_solicitado = "Correção Cirúrgica de Escoliose"
        self.data_cirurgia = date(2026, 3, 15)
        self.tipo_cirurgia = "Eletiva"
        self.duracao_prevista = "4 horas"
        self.condicoes_justificativa = "Curva toracolombar >40 graus"
        self.sinais_sintomas = "Dor lombar, deformidade visível"
        self.resultados_diagnosticos = "RX coluna: curva 45 graus"
        self.assistente = "Dr. Luiz Eduardo Portela"
        self.opme = "Ilizarov Adulto, Caixa 3,5mm"
        self.aparelhos_especiais = None
        self.reserva_sangue = True
        self.quantidade_sangue = "2 unidades"
        self.reserva_uti = True


def test_build_calendar_payload_success(app):
    """Testa montagem correta do payload"""
    with app.app_context():
        patient = MockPatient()
        surgery = MockSurgeryRequest()
        
        payload = build_calendar_payload(surgery, patient)
        
        assert payload['calendarId'] == app.config['GOOGLE_CALENDAR_ID']
        assert payload['title'] == "Correção Cirúrgica de Escoliose"
        assert payload['date'] == "2026-03-15"
        assert payload['orthopedist'] == "Dr. Luiz Eduardo Portela"
        assert payload['needs_icu'] is True
        assert payload['opme_other'] == "Ilizarov Adulto, Caixa 3,5mm"
        assert "João da Silva" in payload['description']
        assert "P12345" in payload['description']
        assert "Escoliose" in payload['description']


def test_build_calendar_payload_missing_title(app):
    """Testa erro quando procedimento não está preenchido"""
    with app.app_context():
        patient = MockPatient()
        surgery = MockSurgeryRequest()
        surgery.procedimento_solicitado = None
        
        with pytest.raises(ValueError, match="Procedimento solicitado é obrigatório"):
            build_calendar_payload(surgery, patient)


def test_build_calendar_payload_missing_date(app):
    """Testa erro quando data não está preenchida"""
    with app.app_context():
        patient = MockPatient()
        surgery = MockSurgeryRequest()
        surgery.data_cirurgia = None
        
        with pytest.raises(ValueError, match="Data da cirurgia é obrigatória"):
            build_calendar_payload(surgery, patient)


def test_build_calendar_preview():
    """Testa formatação do preview"""
    payload = {
        'title': 'Cirurgia de Teste',
        'date': '2026-03-15',
        'description': 'Descrição completa aqui',
        'orthopedist': 'Dr. Teste',
        'opme': ['Item 1', 'Item 2'],
        'opme_other': 'Outros itens',
        'needs_icu': True
    }
    
    preview = build_calendar_preview(payload)
    
    assert preview['title'] == 'Cirurgia de Teste'
    assert '15/03/2026' in preview['date_display']
    assert preview['all_day'] is True
    assert preview['orthopedist'] == 'Dr. Teste'
    assert preview['needs_icu_display'] == 'Sim'
    assert 'Item 1' in preview['opme_display']
    assert 'Outros itens' in preview['opme_display']
    assert preview['description'] == 'Descrição completa aqui'


def test_build_calendar_preview_no_icu():
    """Testa preview quando não precisa UTI"""
    payload = {
        'title': 'Cirurgia de Teste',
        'date': '2026-03-15',
        'description': 'Descrição',
        'orthopedist': 'Dr. Teste',
        'opme': [],
        'opme_other': '',
        'needs_icu': False
    }
    
    preview = build_calendar_preview(payload)
    
    assert preview['needs_icu_display'] == 'Não'
    assert preview['opme_display'] == '—'


@patch('src.services.calendar_scheduler.requests.post')
def test_send_to_calendar_success(mock_post):
    """Testa envio bem-sucedido ao Apps Script"""
    # Mock da resposta do Apps Script
    mock_response = Mock()
    mock_response.json.return_value = {
        'ok': True,
        'eventId': 'abc123',
        'htmlLink': 'https://calendar.google.com/event?eid=abc123',
        'message': 'Evento criado com sucesso'
    }
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    payload = {
        'calendarId': 'test@group.calendar.google.com',
        'title': 'Teste',
        'date': '2026-03-15',
        'description': 'Teste'
    }
    
    success, response, error = send_to_calendar(payload, 'https://script.google.com/test')
    
    assert success is True
    assert response['ok'] is True
    assert response['eventId'] == 'abc123'
    assert error is None
    mock_post.assert_called_once()


@patch('src.services.calendar_scheduler.requests.post')
def test_send_to_calendar_apps_script_error(mock_post):
    """Testa quando Apps Script retorna erro"""
    mock_response = Mock()
    mock_response.json.return_value = {
        'ok': False,
        'error': 'Calendário não encontrado'
    }
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    payload = {'calendarId': 'invalid', 'title': 'Test', 'date': '2026-03-15'}
    
    success, response, error = send_to_calendar(payload, 'https://script.google.com/test')
    
    assert success is False
    assert error == 'Calendário não encontrado'


@patch('src.services.calendar_scheduler.requests.post')
def test_send_to_calendar_timeout(mock_post):
    """Testa timeout de conexão"""
    import requests
    mock_post.side_effect = requests.exceptions.Timeout()
    
    payload = {'calendarId': 'test', 'title': 'Test', 'date': '2026-03-15'}
    
    success, response, error = send_to_calendar(payload, 'https://script.google.com/test')
    
    assert success is False
    assert 'Tempo limite excedido' in error


@patch('src.services.calendar_scheduler.requests.post')
def test_send_to_calendar_connection_error(mock_post):
    """Testa erro de conexão"""
    import requests
    mock_post.side_effect = requests.exceptions.ConnectionError()
    
    payload = {'calendarId': 'test', 'title': 'Test', 'date': '2026-03-15'}
    
    success, response, error = send_to_calendar(payload, 'https://script.google.com/test')
    
    assert success is False
    assert 'Erro de conexão' in error
