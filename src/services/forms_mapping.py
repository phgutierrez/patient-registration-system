"""
Mapeamento de campos do Google Forms
Extraído da URL pública do formulário: 
https://docs.google.com/forms/d/e/1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg/viewform

MAPEAMENTO CORRETO (6 campos obrigatórios):
1. Ortopedista           = entry.754547293      [dropdown obrigatório]
2. Procedimento/Cirurgia = entry.1276090944     [texto curto obrigatório]
3. Data da Cirurgia      = entry.98670871       [date picker obrigatório]
4. Descrição do Paciente = entry.1959704951     [texto longo/parágrafo obrigatório]
5. OPME/Materiais        = entry.1331583755     [checkbox múltiplo]
6. Necessita UTI         = entry.307251533      [radio button obrigatório]
"""

# Mapeamento principal com entry IDs CORRETOS
FORMS_MAPPING = {
    "ortopedista": "entry.754547293",        # Dr. Pedro Henrique, etc
    "procedimento": "entry.1276090944",      # OSTEOTOMIA DA TÍBIA - TESTE, etc
    "data": "entry.98670871",                # 2026-02-02
    "descricao": "entry.1959704951",         # Nome\nIdade\nDados do paciente
    "opme": "entry.1331583755",              # Ilizarov Adulto, Infantil, etc (checkbox)
    "necessita_uti": "entry.307251533"       # Sim/Não
}

def get_forms_mapping():
    """Retorna o mapeamento correto de campos do Forms"""
    return FORMS_MAPPING.copy()


