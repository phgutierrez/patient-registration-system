"""
Serviço para submissão automática de respostas ao Google Forms.

Este módulo substitui a integração direta com Apps Script Web App.
O fluxo agora é:
1. Usuário confirma agendamento
2. Sistema submete resposta ao Google Forms
3. Apps Script da planilha (onFormSubmit) cria evento no calendário
"""

import requests
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from flask import current_app
from difflib import SequenceMatcher
from .forms_mapping import get_forms_mapping


# Arquivo para cache do mapeamento de entry IDs
MAPPING_CACHE_FILE = Path(__file__).parent.parent.parent / 'instance' / 'forms_mapping.json'


def get_public_form_html(form_id: str, timeout: int = 10) -> str:
    """
    Baixa o HTML público do Google Forms para extrair entry IDs.
    
    IMPORTANTE: O form_id DEVE ser o ID PÚBLICO (formato /d/e/<ID_PUBLICO>/viewform),
    NÃO o ID de edição (formato /d/<ID_EDICAO>/edit).
    
    Args:
        form_id: ID do formulário (ex: 1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg)
        timeout: Timeout em segundos
        
    Returns:
        HTML completo do formulário
        
    Raises:
        requests.RequestException: Se falhar ao baixar
    """
    # Tenta ambos os formatos de URL
    urls_to_try = [
        # Formato 1: URL pública (mais comum)
        (f"https://docs.google.com/forms/d/e/{form_id}/viewform", "pública (/d/e/)"),
        # Formato 2: URL direta (se form_id for ID de edição)
        (f"https://docs.google.com/forms/d/{form_id}/viewform", "direta (/d/)"),
    ]
    
    last_error = None
    
    for url, url_type in urls_to_try:
        try:
            current_app.logger.info(f"[?] Tentando URL {url_type}: {url[:60]}...")
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            
            if response.status_code == 200:
                current_app.logger.info(f"[?] Sucesso com URL {url_type} ({len(response.text)} bytes)")
                return response.text
            else:
                current_app.logger.warning(f"[?]️  URL {url_type} retornou status {response.status_code}")
                last_error = f"Status {response.status_code}"
                
        except requests.RequestException as e:
            current_app.logger.warning(f"[?]️  Falha URL {url_type}: {str(e)[:100]}")
            last_error = str(e)
            continue
    
    # Se chegou aqui, nenhuma URL funcionou
    error_msg = (
        f"[?] Falha ao baixar o formulário com ambas as URLs:\n"
        f"   URL pública: https://docs.google.com/forms/d/e/{form_id}/viewform\n"
        f"   URL direta: https://docs.google.com/forms/d/{form_id}/viewform\n"
        f"   Último erro: {last_error}\n\n"
        f"[?]️  DICA: Verifique se GOOGLE_FORMS_EDIT_ID está configurado com o ID PÚBLICO,\n"
        f"   extraído de: https://docs.google.com/forms/d/e/[ID_AQUI]/viewform\n"
        f"   NÃO use o ID de edição de: https://docs.google.com/forms/d/[ID_ERRADO]/edit"
    )
    
    current_app.logger.error(error_msg)
    raise requests.RequestException(error_msg)


def extract_entry_ids(html: str) -> Dict[str, str]:
    """
    Extrai os entry IDs do HTML do Google Forms.
    
    O Google Forms moderno usa estruturas JSON no HTML da página.
    Esta função tenta múltiplos padrões de extração.
    
    Args:
        html: HTML completo do formulário
        
    Returns:
        Dicionário mapeando campo -> entry ID
        Exemplo: {
            "ortopedista": "entry.123456",
            "procedimento": "entry.234567",
            ...
        }
    """
    mapping = {}
    
    # **PADRÃO PRINCIPAL**: Extrair TODOS os entry.XXXX do HTML
    # Isso funciona para qualquer versão do Google Forms
    all_entry_pattern = r'entry\.(\d+)'
    all_entries = set()
    
    for match in re.finditer(all_entry_pattern, html):
        entry_id = f"entry.{match.group(1)}"
        all_entries.add(entry_id)
    
    entries_list = sorted(list(all_entries), key=lambda x: int(x.split('.')[-1]))
    current_app.logger.info(f"[OK] Encontrados {len(entries_list)} entry IDs no HTML: {entries_list}")
    
    # Se encontrou muitos entry IDs (mais de 30), há algo errado
    if len(entries_list) > 30:
        current_app.logger.warning(f"[WARNING] Muitos entry IDs encontrados ({len(entries_list)}), filtrando...")
        # Pegar apenas os primeiros que parecem ser campos principais
        entries_list = entries_list[:10]
    
    # Mapear para os campos conhecidos - MAS ACEITAR MAPEAMENTOS PARCIAIS
    field_names = [
        "ortopedista",      # Campo 1: Dropdown
        "procedimento",     # Campo 2: Texto curto
        "data",             # Campo 3: Date  (OPCIONAL)
        "descricao",        # Campo 4: Texto longo  (OPCIONAL)
        "opme",             # Campo 5: Checkbox  (OPCIONAL)
        "necessita_uti"     # Campo 6: Radio (Sim/Não)  (OPCIONAL)
    ]
    
    # Mapeamento inteligente: os fields obrigatórios são os 2 primeiros
    mapping = {}
    for i, field_name in enumerate(field_names):
        if i < len(entries_list):
            mapping[field_name] = entries_list[i]
            current_app.logger.info(f"  [OK] Mapeado {field_name:15} -> {entries_list[i]}")
        else:
            current_app.logger.info(f"  ─ Campo '{field_name}' não encontrado (esperado índice {i}, temos {len(entries_list)})")
    
    # Buscar campo "Outro" para OPME
    opme_outro_pattern = r'entry\.(\d+)\.other_option_response'
    opme_outro_match = re.search(opme_outro_pattern, html)
    if opme_outro_match:
        mapping["opme_outro"] = f"entry.{opme_outro_match.group(1)}.other_option_response"
        current_app.logger.info(f"  [OK] Mapeado opme_outro        -> {mapping['opme_outro']}")
    
    current_app.logger.info(f"\n[INFO] RESULTADO FINAL:")
    current_app.logger.info(f"   Total de campos mapeados: {len(mapping)}")
    current_app.logger.info(f"   Campos obrigatórios: ortopedista={mapping.get('ortopedista', 'NAO_ENCONTRADO')}, procedimento={mapping.get('procedimento', 'NAO_ENCONTRADO')}")
    current_app.logger.info(f"   Campos opcionais: {[k for k in mapping.keys() if k not in ['ortopedista', 'procedimento']]}")
    current_app.logger.info(f"   Mapeamento completo: {mapping}\n")
    
    return mapping


def save_mapping_cache(mapping: Dict[str, str]):
    """
    Salva o mapeamento de entry IDs em arquivo JSON para cache.
    
    Args:
        mapping: Dicionário com o mapeamento campo -> entry ID
    """
    MAPPING_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    cache_data = {
        "mapping": mapping,
        "updated_at": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    with open(MAPPING_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    
    current_app.logger.info(f"Mapeamento salvo em {MAPPING_CACHE_FILE}")


def load_mapping_cache() -> Optional[Dict[str, str]]:
    """
    Carrega o mapeamento de entry IDs do cache.
    
    Returns:
        Dicionário com mapping ou None se não existir/inválido
    """
    if not MAPPING_CACHE_FILE.exists():
        current_app.logger.info("Cache de mapeamento não encontrado")
        return None
    
    try:
        with open(MAPPING_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        mapping = cache_data.get("mapping")
        updated_at = cache_data.get("updated_at")
        
        current_app.logger.info(f"Mapeamento carregado do cache (atualizado em {updated_at})")
        return mapping
        
    except (json.JSONDecodeError, IOError) as e:
        current_app.logger.error(f"Erro ao ler cache: {e}")
        return None


def get_or_refresh_mapping(form_id: str, force_refresh: bool = False) -> Dict[str, str]:
    """
    Obtém o mapeamento de entry IDs do Google Forms.
    
    MAPEAMENTO CORRETO (extraído manualmente da URL pública do Forms):
    - entry.754547293 = Ortopedista (dropdown)
    - entry.1331583755 = Procedimento (checkbox com múltiplos valores)
    - entry.98670871 = Data (date picker)
    - entry.1276090944 = Descrição (long text)
    - entry.1959704951 = OPME Outro (text field)
    - entry.307251533 = Necessita UTI (radio button)
    
    Args:
        form_id: ID do formulário (ignorado)
        force_refresh: Se True, ignora cache (ignorado)
        
    Returns:
        Dicionário com mapping campo -> entry ID
    """
    current_app.logger.info("[INFO] Usando mapeamento correto de entry IDs do Forms")
    
    # Usar mapeamento correto
    mapping = get_forms_mapping()
    
    current_app.logger.info(f"[OK] Mapeamento obtido: {len(mapping)} campos")
    current_app.logger.info(f"     Campos: {list(mapping.keys())}")
    
    # Salvar em cache para referência
    save_mapping_cache(mapping)
    
    return mapping


def find_matching_orthopedist(user_full_name: str) -> str:
    """
    Encontra o ortopedista mais próximo do nome do usuário ativo usando fuzzy matching.
    
    A lista de ortopedistas vem das opções do dropdown no Google Forms.
    Faz matching do nome completo do usuário com as opções disponíveis.
    
    Args:
        user_full_name: Nome completo do usuário ativo (ex: "Dr. João Silva")
        
    Returns:
        Nome do ortopedista mais próximo ou "Não informado" se não encontrar match
    """
    
    # Lista de ortopedistas possíveis no dropdown do Forms
    # Esta lista deve ser atualizada conforme os ortopedistas cadastrados no Forms
    possible_orthopedists = [
        "Dr. Laecio Damaceno",
        "Dr. Sávio Bruno",
        "Dr. Pedro Henrique",
        "Dr. Brauner Cavalcanti",
        "Dr. André Cristiano",
        "Dr. Bruno Montenegro",
        "Dr. Eduardo Lyra",
        "Dr. Jocemir",
        "Dr. Luiz Portela",
        "Dr. Francisco Neto",
        "Dr. Bartolomeu",
    ]
    
    # Normalizar nome do usuário
    user_name_normalized = user_full_name.strip().lower()
    
    # Se já tem "Dr." ou similar, remover para comparação
    prefixes_to_remove = ["dr.", "dr", "prof.", "prof", "sr.", "sr", "dra.", "dra"]
    for prefix in prefixes_to_remove:
        if user_name_normalized.startswith(prefix):
            user_name_normalized = user_name_normalized[len(prefix):].strip()
    
    # Buscar o melhor match
    best_match = None
    best_ratio = 0.0
    
    for orthopedist in possible_orthopedists:
        # Normalizar ortopedista (removendo "Dr." também)
        ortho_normalized = orthopedist.lower()
        for prefix in prefixes_to_remove:
            if ortho_normalized.startswith(prefix):
                ortho_normalized = ortho_normalized[len(prefix):].strip()
                break
        
        # Calcular similarity ratio
        ratio = SequenceMatcher(None, user_name_normalized, ortho_normalized).ratio()
        
        # Se o user_name aparece contido no ortho_name, aumentar score
        if user_name_normalized in ortho_normalized or ortho_normalized in user_name_normalized:
            ratio = max(ratio, 0.8)
        
        # Match por partes do nome (ex: "Pedro Freitas" vs "Pedro Henrique")
        user_parts = user_name_normalized.split()
        ortho_parts = ortho_normalized.split()
        
        # Se o primeiro nome corresponde, aumentar score
        if user_parts and ortho_parts and user_parts[0] == ortho_parts[0]:
            ratio = max(ratio, 0.7)
        
        # Se alguma parte do nome do usuário aparece no ortopedista
        for user_part in user_parts:
            if len(user_part) > 2 and user_part in ortho_normalized:
                ratio = max(ratio, 0.65)
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = orthopedist
    
    # Se encontrou um match com score >= 0.5 (50% de similaridade), usar
    if best_ratio >= 0.5 and best_match:
        current_app.logger.info(
            f"Fuzzy match encontrado: '{user_full_name}' -> '{best_match}' (ratio: {best_ratio:.2%})"
        )
        return best_match
    
    # Se não encontrou, tentar match simples por sobrenome
    user_parts = user_full_name.split()
    if len(user_parts) > 1:
        last_name = user_parts[-1].lower()
        for orthopedist in possible_orthopedists:
            if last_name in orthopedist.lower():
                current_app.logger.info(
                    f"Match por sobrenome encontrado: '{user_full_name}' -> '{orthopedist}'"
                )
                return orthopedist
    
    # Fallback: retornar primeiro nome ou "Não informado"
    current_app.logger.warning(
        f"Nenhum match fuzzy encontrado para '{user_full_name}' (melhor ratio: {best_ratio:.2%})"
    )
    return "Não informado"


def find_matching_opme(opme_text: str) -> Tuple[List[str], str]:
    """
    Encontra as opções de OPME mais próximas do texto livre usando fuzzy matching.
    
    Args:
        opme_text: Texto livre do campo OPME do sistema
        
    Returns:
        Tupla (lista de opções selecionadas, texto para campo "Outro")
        Exemplo: (["Caixa 3,5mm", "Placa em 8"], "")
                 (["Outro"], "Prótese especial importada")
    """
    # Opções disponíveis no Google Forms
    possible_opme_options = [
        "Ilizarov Adulto",
        "Ilizarov Infantil",
        "Caixa 3,5mm",
        "Caixa 4,5mm",
        "Placa angulada",
        "Fios de Kirschner",
        "Parafuso Canulado",
        "Âncora",
        "Placa em 8",
        "Artrodese Coluna",
    ]
    
    if not opme_text or opme_text.strip() == "":
        return ([], "")
    
    opme_normalized = opme_text.lower().strip()
    matched_options = []
    remaining_text = opme_text
    
    # Mapa de keywords - TODAS devem estar presentes para dar match
    keywords_map = {
        "Ilizarov Adulto": [["ilizarov", "adulto"]],
        "Ilizarov Infantil": [["ilizarov", "infantil"], ["ilizarov", "criança"], ["ilizarov", "pediátrico"]],
        "Caixa 3,5mm": [["3.5"], ["3,5"], ["caixa", "3.5"], ["caixa", "3,5"]],
        "Caixa 4,5mm": [["4.5"], ["4,5"], ["caixa", "4.5"], ["caixa", "4,5"]],
        "Placa angulada": [["placa", "angulada"], ["angulada"]],
        "Fios de Kirschner": [["fios", "kirschner"], ["fio", "k"], ["kirschner"]],
        "Parafuso Canulado": [["parafuso", "canulado"], ["canulado"]],
        "Âncora": [["ancora"], ["âncora"]],
        "Placa em 8": [["placa", "8"], ["placa em 8"]],
        "Artrodese Coluna": [["artrodese", "coluna"], ["artrodese"]],
    }
    
    # Tentar fazer match com cada opção
    for option in possible_opme_options:
        option_normalized = option.lower()
        
        # Match exato (case insensitive)
        if option_normalized in opme_normalized or opme_normalized in option_normalized:
            # Verificar se é match legítimo (não match parcial indesejado)
            # Por exemplo, "3,5" não deve dar match em "4,5"
            if option == "Caixa 4,5mm" and ("3.5" in opme_normalized or "3,5" in opme_normalized):
                continue
            if option == "Caixa 3,5mm" and ("4.5" in opme_normalized or "4,5" in opme_normalized):
                continue
            if option == "Ilizarov Infantil" and ("adulto" in opme_normalized):
                continue
            if option == "Ilizarov Adulto" and ("infantil" in opme_normalized or "criança" in opme_normalized):
                continue
                
            matched_options.append(option)
            remaining_text = remaining_text.replace(option, "").strip()
            continue
        
        # Fuzzy match por combinações de keywords
        keyword_combos = keywords_map.get(option, [])
        for keyword_combo in keyword_combos:
            # TODAS as keywords da combinação devem estar presentes
            if all(keyword.lower() in opme_normalized for keyword in keyword_combo):
                # Verificar exclusões para evitar falsos positivos
                should_skip = False
                
                if option == "Ilizarov Infantil" and "adulto" in opme_normalized:
                    should_skip = True
                if option == "Ilizarov Adulto" and any(x in opme_normalized for x in ["infantil", "criança", "pediátrico"]):
                    should_skip = True
                if option == "Caixa 4,5mm" and ("3.5" in opme_normalized or "3,5" in opme_normalized):
                    should_skip = True
                if option == "Caixa 3,5mm" and ("4.5" in opme_normalized or "4,5" in opme_normalized):
                    should_skip = True
                
                if not should_skip:
                    matched_options.append(option)
                    # Remover keywords para análise posterior
                    for kw in keyword_combo:
                        remaining_text = remaining_text.lower().replace(kw.lower(), "").strip()
                    break
    
    # O que sobrou vai para "Outro"
    remaining_text = remaining_text.replace(",", "").replace(";", "").strip()
    
    # Se não encontrou nenhum match ou tem texto sobrando significativo, usar "Outro"
    if not matched_options or (remaining_text and len(remaining_text) > 3):
        other_text = remaining_text if remaining_text else opme_text
        current_app.logger.info(f"OPME sem match direto, usando 'Outro': {other_text}")
        return ([], other_text)
    
    current_app.logger.info(f"OPME matched: {matched_options}")
    return (matched_options, "")


def build_forms_payload(surgery_request, patient) -> Dict[str, any]:
    """
    Constrói o payload de dados para submissão ao Google Forms.
    
    Args:
        surgery_request: Objeto SurgeryRequest
        patient: Objeto Patient
        
    Returns:
        Dicionário com os dados formatados para o Forms:
        {
            "orthopedist": "Dr. ...",
            "procedure_title": "OSTEOTOMIA ...",
            "date": "2026-02-04",
            "full_description": "Nome: ...\nIdade: ...",
            "opme": ["Caixa 3,5mm", "Placa em 8"],
            "opme_other": "texto livre",
            "needs_icu": "Sim"
        }
    """
    from datetime import date
    from flask_login import current_user
    
    # Ortopedista responsável - usa fuzzy matching com usuário ativo
    orthopedist = find_matching_orthopedist(current_user.full_name)
    
    # Procedimento (título do evento)
    procedure_title = surgery_request.procedimento_solicitado
    if not procedure_title:
        raise ValueError("Procedimento solicitado é obrigatório")
    
    # Data da cirurgia
    surgery_date = surgery_request.data_cirurgia
    if not surgery_date:
        raise ValueError("Data da cirurgia é obrigatória")
    
    # Formatar data no formato aceito pelo Forms (YYYY-MM-DD ou DD/MM/YYYY)
    if isinstance(surgery_date, str):
        date_str = surgery_date
    elif isinstance(surgery_date, date):
        date_str = surgery_date.strftime("%Y-%m-%d")
    else:
        date_str = str(surgery_date)
    
    # Descrição completa com o layout solicitado
    description_parts = []
    
    # Dados do paciente no layout especificado
    if patient:
        # Nome
        if patient.nome:
            description_parts.append(f"Nome: {patient.nome}")
        
        # Data de nascimento (formatada)
        if patient.data_nascimento:
            data_formatted = patient.data_nascimento.strftime("%d/%m/%Y")
            description_parts.append(f"Data de nascimento: {data_formatted}")
        
        # Diagnóstico
        if patient.diagnostico:
            description_parts.append(f"Diagnóstico: {patient.diagnostico}")
        
        # Prontuário
        if patient.prontuario:
            description_parts.append(f"Nº Prontuário: {patient.prontuario}")
        
        # Contato/Telefone
        if patient.contato:
            description_parts.append(f"Contato: {patient.contato}")
    
    # OPME - fazer fuzzy matching com as opções do Forms
    opme_list = []
    
    if surgery_request.opme:
        opme_list, opme_other_text = find_matching_opme(surgery_request.opme)
    else:
        opme_other_text = ""
    
    # UTI - obrigatório no Forms
    needs_icu = "Sim" if surgery_request.reserva_uti else "Não"
    
    # Descrição final com dados do paciente (será enviada como texto longo)
    full_description = "\n".join(description_parts)
    
    payload = {
        "orthopedist": orthopedist,
        "procedure_title": procedure_title,
        "date": date_str,
        "full_description": full_description,
        "opme": opme_list,  # Lista para checkbox
        "needs_icu": needs_icu,
        "opme_other": opme_other_text
    }
    
    current_app.logger.info(f"Payload construído: procedimento={procedure_title}, data={date_str}")
    
    return payload


def submit_form(form_id: str, payload: Dict[str, any], timeout: int = 10) -> Tuple[bool, str, int]:
    """
    Submete uma resposta ao Google Forms.
    
    Args:
        form_id: ID do formulário
        payload: Dicionário com dados do build_forms_payload()
        timeout: Timeout em segundos
        
    Returns:
        Tupla (sucesso: bool, mensagem: str, status_code: int)
        
    Status Codes:
        200/302: Sucesso (Forms aceita resposta)  
        400: Payload inválido ou entry IDs incorretos
        403: Permissão negada (Forms fechado)
        404: PUBLIC_ID inválido ou Forms não encontrado
        502: Erro de rede ou timeout
    """
    try:
        # Determinar PUBLIC_ID do Forms
        current_app.logger.info("[INFO] Iniciando submissao ao Google Forms...")
        public_id = current_app.config.get('GOOGLE_FORMS_PUBLIC_ID')
        view_url = current_app.config.get('GOOGLE_FORMS_VIEWFORM_URL')

        # Se não tiver public_id, tentar extrair de view_url
        if not public_id and view_url:
            m = re.search(r"/d/e/([A-Za-z0-9_-]+)/", view_url)
            if m:
                public_id = m.group(1)

        if not public_id:
            # Não podemos prosseguir sem PUBLIC_ID público
            current_app.logger.error("GOOGLE_FORMS_PUBLIC_ID ou GOOGLE_FORMS_VIEWFORM_URL não configurado")
            return False, 'GOOGLE_FORMS_PUBLIC_ID não configurado. Configure GOOGLE_FORMS_PUBLIC_ID ou GOOGLE_FORMS_VIEWFORM_URL no .env', 400

        # Obter mapeamento de entry IDs (usa o mapeamento estático ou extraído)
        mapping = get_or_refresh_mapping(public_id)
        current_app.logger.info(f"[OK] Mapeamento obtido: {len(mapping)} campos")
        
        # Montar dados do POST
        # Para campos simples: {entry.XXX: valor}
        # Para checkbox: lista de tuplas [(entry.XXX, valor1), (entry.XXX, valor2)]
        
        form_data = []
        
        # Ortopedista (dropdown)
        if "ortopedista" in mapping:
            form_data.append((mapping["ortopedista"], payload["orthopedist"]))
            current_app.logger.info(f"   [OK] Ortopedista: {payload['orthopedist']}")
        else:
            current_app.logger.warning("   [X] Campo 'ortopedista' nao mapeado")
        
        # Procedimento (texto curto)
        if "procedimento" in mapping:
            form_data.append((mapping["procedimento"], payload["procedure_title"]))
            current_app.logger.info(f"   [OK] Procedimento: {payload['procedure_title']}")
        else:
            current_app.logger.warning("   [X] Campo 'procedimento' nao mapeado")
        
        # Data (date)
        if "data" in mapping:
            form_data.append((mapping["data"], payload["date"]))
            current_app.logger.info(f"   [OK] Data: {payload['date']}")
        else:
            current_app.logger.warning("   [X] Campo 'data' nao mapeado")
        
        # Descrição (texto longo)
        if "descricao" in mapping:
            form_data.append((mapping["descricao"], payload["full_description"]))
            current_app.logger.info(f"   [OK] Descricao: {len(payload['full_description'])} caracteres")
        else:
            current_app.logger.warning("   [X] Campo 'descricao' nao mapeado")
        
        # OPME (checkbox - múltiplos valores)
        if "opme" in mapping and payload.get("opme"):
            for opme_item in payload["opme"]:
                # Não incluir "Outro: ..." na lista de checkboxes
                if not opme_item.startswith("Outro:"):
                    form_data.append((mapping["opme"], opme_item))
            current_app.logger.info(f"   [OK] OPME: {len(payload.get('opme', []))} itens")
        else:
            if "opme" not in mapping:
                current_app.logger.warning("   [X] Campo 'opme' nao mapeado")
            else:
                current_app.logger.info("   [i] OPME vazio")

        # Opção 'Outro' para OPME (campo de texto extra)
        if mapping.get('opme_outro') and payload.get('opme_other'):
            # mapping['opme_outro'] pode ter sufixo like 'entry.123.other_option_response'
            form_data.append((mapping['opme_outro'], payload.get('opme_other')))
            current_app.logger.info(f"   [OK] OPME outro: {payload.get('opme_other')}")
        
        # Necessita UTI (radio button)
        if "necessita_uti" in mapping:
            form_data.append((mapping["necessita_uti"], payload["needs_icu"]))
            current_app.logger.info(f"   [OK] Necessita UTI: {payload['needs_icu']}")
        else:
            current_app.logger.warning("   [X] Campo 'necessita_uti' nao mapeado")
        
        # Resumo
        current_app.logger.info(f"\n[INFO] Resumo da submissao:")
        current_app.logger.info(f"   Total de campos: {len(form_data)}")
        current_app.logger.info(f"   Dados: {form_data}\n")
        
        # URL de submissão
        submit_url = f"https://docs.google.com/forms/d/e/{public_id}/formResponse"

        current_app.logger.info(f"[INFO] Submetendo ao Forms: {submit_url}")

        # POST com x-www-form-urlencoded e headers apropriados
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (compatible)'
        }

        response = requests.post(
            submit_url,
            data=form_data,
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )

        status = response.status_code

        # Aceitar 200 ou 302 como sucesso (Forms pode redirecionar)
        if status in (200, 302):
            current_app.logger.info(f"[OK] Forms submetido com sucesso (status {status})")
            return True, 'Resposta enviada ao Google Forms com sucesso', status

        # Erros específicos
        if status == 404:
            current_app.logger.error(f"Forms retornou 404 - URL inválida: {submit_url}")
            return False, 'Forms URL inválida (PUBLIC_ID incorreto ou formulário privado)', 404
        if status == 403:
            current_app.logger.error('Forms retornou 403 - acesso negado (form privado)')
            return False, 'Formulário privado ou sem permissão de envio (403)', 403
        if status == 400:
            current_app.logger.error('Forms retornou 400 - payload inválido (entry IDs)')
            return False, 'Payload inválido para o Google Forms (verifique mapeamento entry IDs)', 400

        # Outros códigos
        current_app.logger.warning(f"Forms retornou status inesperado: {status}")
        current_app.logger.debug(f"Response: {response.text[:1000]}")
        return False, f'Google Forms retornou status {status}', status
            
    except requests.Timeout:
        current_app.logger.error("Timeout ao submeter Forms")
        return False, "Timeout ao enviar para o Google Forms (verifique sua conexão)", 504
    
    except requests.ConnectionError as e:
        current_app.logger.error(f"Erro de conexão ao submeter Forms: {e}")
        return False, "Erro de conexão com Google Forms. Verifique sua conexão com a internet.", 502
    
    except requests.RequestException as e:
        current_app.logger.error(f"Erro ao submeter Forms: {e}")
        return False, f"Erro ao enviar para Google Forms: {str(e)}", 502
        
    except KeyError as e:
        current_app.logger.error(f"Campo obrigatório não encontrado no Forms: {e}")
        return False, f"Erro: Campo '{str(e)}' não encontrado no Forms. Verifique se o formulário está configurado corretamente.", 502
        
    except Exception as e:
        current_app.logger.error(f"Erro inesperado ao submeter Forms: {e}", exc_info=True)
        return False, f"Erro inesperado ao enviar para o Google Forms: {str(e)}", 500
