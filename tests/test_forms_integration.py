"""
Teste de integração: Submissão ao Google Forms

Este teste valida o fluxo completo de agendamento via Forms:
1. Build payload
2. Extração de entry IDs
3. Submissão ao Forms (mock)

USO:
    pytest tests/test_forms_integration.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.forms_service import (
    build_forms_payload,
    extract_entry_ids,
    submit_form,
    get_or_refresh_mapping
)


class MockPatient:
    """Mock do modelo Patient para testes."""
    def __init__(self):
        self.nome_completo = "João Silva"
        self.data_nascimento = "1980-05-15"
        self.prontuario = "12345"
        self.telefone = "(85) 98888-7777"


class MockSurgeryRequest:
    """Mock do modelo SurgeryRequest para testes."""
    def __init__(self):
        self.ortopedista_responsavel = "Dr. Pedro Henrique"
        self.procedimento_solicitado = "OSTEOTOMIA TIBIAL ALTA"
        self.data_cirurgia = "2026-02-10"
        self.diagnostico = "Gonartrose medial"
        self.observacoes = "Paciente com histórico de hipertensão"
        self.opme_ilizarov_adulto = False
        self.opme_ilizarov_infantil = False
        self.opme_caixa_35mm = True
        self.opme_placa_em_8 = True
        self.opme_hastes_im = False
        self.opme_outros = "Parafusos especiais"
        self.necessita_vaga_uti = True


def test_build_forms_payload_success():
    """Testa construção de payload com dados válidos."""
    surgery = MockSurgeryRequest()
    patient = MockPatient()
    
    payload = build_forms_payload(surgery, patient)
    
    assert payload['orthopedist'] == "Dr. Pedro Henrique"
    assert payload['procedure_title'] == "OSTEOTOMIA TIBIAL ALTA"
    assert payload['date'] == "2026-02-10"
    assert payload['needs_icu'] == "Sim"
    assert "Caixa 3,5mm" in payload['opme']
    assert "Placa em 8" in payload['opme']
    assert payload['opme_other'] == "Parafusos especiais"
    assert "João Silva" in payload['full_description']
    assert "12345" in payload['full_description']  # prontuário


def test_build_forms_payload_missing_procedure():
    """Testa erro quando procedimento está faltando."""
    surgery = MockSurgeryRequest()
    surgery.procedimento_solicitado = None
    patient = MockPatient()
    
    with pytest.raises(ValueError, match="Procedimento solicitado é obrigatório"):
        build_forms_payload(surgery, patient)


def test_build_forms_payload_missing_date():
    """Testa erro quando data está faltando."""
    surgery = MockSurgeryRequest()
    surgery.data_cirurgia = None
    patient = MockPatient()
    
    with pytest.raises(ValueError, match="Data da cirurgia é obrigatória"):
        build_forms_payload(surgery, patient)


def test_build_forms_payload_no_opme():
    """Testa payload quando nenhum OPME está selecionado."""
    surgery = MockSurgeryRequest()
    surgery.opme_caixa_35mm = False
    surgery.opme_placa_em_8 = False
    surgery.opme_outros = None
    patient = MockPatient()
    
    payload = build_forms_payload(surgery, patient)
    
    assert payload['opme'] == []
    assert payload['opme_other'] == ""


def test_build_forms_payload_no_uti():
    """Testa payload quando UTI não é necessária."""
    surgery = MockSurgeryRequest()
    surgery.necessita_vaga_uti = False
    patient = MockPatient()
    
    payload = build_forms_payload(surgery, patient)
    
    assert payload['needs_icu'] == "Não"


def test_extract_entry_ids_basic():
    """Testa extração de entry IDs de HTML simples."""
    html = '''
    <form>
        <input name="entry.123456" type="text" />
        <input name="entry.234567" type="text" />
        <input name="entry.345678" type="date" />
        <textarea name="entry.456789"></textarea>
        <input name="entry.567890" type="checkbox" />
        <input name="entry.567890.other_option_response" type="text" />
        <input name="entry.678901" type="radio" />
    </form>
    '''
    
    mapping = extract_entry_ids(html)
    
    assert "ortopedista" in mapping
    assert "procedimento" in mapping
    assert "data" in mapping
    assert "descricao" in mapping
    assert "opme" in mapping
    assert "necessita_uti" in mapping
    assert "opme_outro" in mapping
    
    assert mapping["ortopedista"] == "entry.123456"
    assert mapping["opme_outro"] == "entry.567890.other_option_response"


@patch('src.services.forms_service.requests.post')
@patch('src.services.forms_service.get_or_refresh_mapping')
def test_submit_form_success(mock_mapping, mock_post):
    """Testa submissão bem-sucedida ao Forms."""
    # Mock do mapeamento
    mock_mapping.return_value = {
        "ortopedista": "entry.111",
        "procedimento": "entry.222",
        "data": "entry.333",
        "descricao": "entry.444",
        "opme": "entry.555",
        "necessita_uti": "entry.666"
    }
    
    # Mock da resposta HTTP (Forms retorna 302 em sucesso)
    mock_response = MagicMock()
    mock_response.status_code = 302
    mock_post.return_value = mock_response
    
    # Payload de teste
    payload = {
        "orthopedist": "Dr. Teste",
        "procedure_title": "Teste",
        "date": "2026-02-10",
        "full_description": "Descrição teste",
        "opme": ["Caixa 3,5mm"],
        "opme_other": "",
        "needs_icu": "Sim"
    }
    
    success, message = submit_form("test-form-id", payload, timeout=10)
    
    assert success is True
    assert "sucesso" in message.lower()
    mock_post.assert_called_once()


@patch('src.services.forms_service.requests.post')
@patch('src.services.forms_service.get_or_refresh_mapping')
def test_submit_form_timeout(mock_mapping, mock_post):
    """Testa timeout na submissão ao Forms."""
    mock_mapping.return_value = {
        "ortopedista": "entry.111",
        "procedimento": "entry.222",
        "data": "entry.333",
        "descricao": "entry.444",
        "opme": "entry.555",
        "necessita_uti": "entry.666"
    }
    
    # Simular timeout
    import requests
    mock_post.side_effect = requests.Timeout("Connection timeout")
    
    payload = {
        "orthopedist": "Dr. Teste",
        "procedure_title": "Teste",
        "date": "2026-02-10",
        "full_description": "Descrição teste",
        "opme": [],
        "opme_other": "",
        "needs_icu": "Não"
    }
    
    success, message = submit_form("test-form-id", payload, timeout=10)
    
    assert success is False
    assert "timeout" in message.lower()


@patch('src.services.forms_service.requests.post')
@patch('src.services.forms_service.get_or_refresh_mapping')
def test_submit_form_connection_error(mock_mapping, mock_post):
    """Testa erro de conexão na submissão ao Forms."""
    mock_mapping.return_value = {
        "ortopedista": "entry.111",
        "procedimento": "entry.222",
        "data": "entry.333",
        "descricao": "entry.444",
        "opme": "entry.555",
        "necessita_uti": "entry.666"
    }
    
    # Simular erro de conexão
    import requests
    mock_post.side_effect = requests.ConnectionError("Network unreachable")
    
    payload = {
        "orthopedist": "Dr. Teste",
        "procedure_title": "Teste",
        "date": "2026-02-10",
        "full_description": "Descrição teste",
        "opme": [],
        "opme_other": "",
        "needs_icu": "Não"
    }
    
    success, message = submit_form("test-form-id", payload, timeout=10)
    
    assert success is False
    assert "conexão" in message.lower()


@patch('src.services.forms_service.requests.post')
@patch('src.services.forms_service.get_or_refresh_mapping')
def test_submit_form_multiple_opme(mock_mapping, mock_post):
    """Testa submissão com múltiplos itens OPME (checkbox)."""
    mock_mapping.return_value = {
        "ortopedista": "entry.111",
        "procedimento": "entry.222",
        "data": "entry.333",
        "descricao": "entry.444",
        "opme": "entry.555",
        "opme_outro": "entry.555.other_option_response",
        "necessita_uti": "entry.666"
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    payload = {
        "orthopedist": "Dr. Teste",
        "procedure_title": "Teste",
        "date": "2026-02-10",
        "full_description": "Descrição teste",
        "opme": ["Ilizarov Adulto", "Caixa 3,5mm", "Placa em 8"],
        "opme_other": "Item customizado",
        "needs_icu": "Sim"
    }
    
    success, message = submit_form("test-form-id", payload, timeout=10)
    
    assert success is True
    
    # Verificar que post foi chamado com lista de tuplas
    call_args = mock_post.call_args
    form_data = call_args[1]['data']
    
    # Deve ter múltiplas entradas para entry.555 (checkbox)
    opme_entries = [item for item in form_data if item[0] == 'entry.555']
    assert len(opme_entries) == 3
    
    # Deve ter entrada para "Outro"
    opme_outro_entries = [item for item in form_data if item[0] == 'entry.555.other_option_response']
    assert len(opme_outro_entries) == 1
    assert opme_outro_entries[0][1] == "Item customizado"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
