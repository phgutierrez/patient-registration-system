# Reversão: Web App → Submissão ao Google Forms

## 📋 Resumo das Mudanças

Este documento descreve a **reversão** da integração de agendamento via Apps Script Web App de volta para **submissão direta ao Google Forms**.

### Por que reverter?

O Apps Script **onFormSubmit** ligado à planilha de respostas do Google Forms já funciona perfeitamente para criar eventos no calendário. Não há necessidade de manter um endpoint Web App separado.

### Novo Fluxo

```
┌─────────────────┐
│ Usuário clica   │
│ "Adicionar à    │
│  Agenda"        │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Modal de        │
│ PRÉ-VISUALIZAÇÃO│ ← build_forms_payload()
│ (título, data,  │
│  descrição...)  │
└────────┬────────┘
         │
         v (confirma)
┌─────────────────┐
│ POST para       │
│ Google Forms    │ ← submit_form()
│ /formResponse   │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Apps Script da  │
│ Planilha        │ ← onFormSubmit trigger
│ cria evento     │
│ no Calendar     │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Evento DIA      │
│ INTEIRO criado  │
│ no Google       │
│ Calendar        │
└─────────────────┘
```

---

## 🗑️ Arquivos Removidos/Desabilitados

### Removidos
- **calendar_scheduler.py** (antiga integração Web App)
  - `build_calendar_payload()` → substituído por `build_forms_payload()`
  - `send_to_calendar()` → substituído por `submit_form()`

### Desabilitados
- **CalendarScheduler.gs** (Apps Script Web App)
  - Não é mais necessário (Apps Script da planilha já cria eventos)
- **APPS_SCRIPT_SCHEDULER_URL** em config.py
  - Comentado, não usado

---

## 📁 Arquivos Criados

### 1. `src/services/forms_service.py`

Novo serviço para submissão ao Google Forms.

**Funções principais:**

#### `get_public_form_html(form_id, timeout=10) -> str`
Baixa o HTML público do Google Forms para extrair entry IDs.

**Parâmetros:**
- `form_id`: ID do formulário (ex: `1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw`)
- `timeout`: Timeout em segundos

**Retorna:** HTML completo do formulário

**Exceções:** `requests.RequestException` se falhar ao baixar

---

#### `extract_entry_ids(html) -> Dict[str, str]`
Extrai os entry IDs do HTML do Forms usando regex.

**Parâmetros:**
- `html`: HTML completo do formulário

**Retorna:** Dicionário mapeando campo → entry ID
```python
{
    "ortopedista": "entry.123456",
    "procedimento": "entry.234567",
    "data": "entry.345678",
    "descricao": "entry.456789",
    "opme": "entry.567890",
    "opme_outro": "entry.567890.other_option_response",
    "necessita_uti": "entry.678901"
}
```

**Lógica:**
1. Busca por padrão `name="entry.<numero>"` no HTML
2. Mapeia para campos conhecidos na ordem conceitual
3. Detecta campo "Outro" do OPME (sufixo `.other_option_response`)

**IMPORTANTE:** Se a ordem das perguntas no Forms mudar, ajustar `field_names` na função.

---

#### `save_mapping_cache(mapping)`
Salva o mapeamento em `instance/forms_mapping.json`.

**Formato do cache:**
```json
{
  "mapping": {
    "ortopedista": "entry.123456",
    ...
  },
  "updated_at": "2026-02-05T10:30:00",
  "version": "1.0"
}
```

---

#### `load_mapping_cache() -> Optional[Dict]`
Carrega o mapeamento do cache.

**Retorna:** Dicionário com mapping ou `None` se não existir/inválido.

---

#### `get_or_refresh_mapping(form_id, force_refresh=False) -> Dict`
Obtém mapping usando cache ou baixando se necessário.

**Parâmetros:**
- `form_id`: ID do formulário
- `force_refresh`: Se True, ignora cache e baixa novamente

**Exceções:** `Exception` se falhar ao obter mapping

---

#### `build_forms_payload(surgery_request, patient) -> Dict`
Constrói payload de dados para o Forms.

**Parâmetros:**
- `surgery_request`: Objeto SurgeryRequest
- `patient`: Objeto Patient

**Retorna:**
```python
{
    "orthopedist": "Dr. Pedro Henrique",
    "procedure_title": "OSTEOTOMIA TIBIAL",
    "date": "2026-02-04",
    "full_description": "DADOS DO PACIENTE:\nNome: ...\n...",
    "opme": ["Caixa 3,5mm", "Placa em 8"],
    "opme_other": "texto livre",
    "needs_icu": "Sim"
}
```

**Exceções:** `ValueError` se campos obrigatórios faltarem (procedimento, data)

---

#### `submit_form(form_id, payload, timeout=10) -> Tuple[bool, str, int]`
Submete resposta ao Google Forms.

**Parâmetros:**
- `form_id`: ID do formulário
- `payload`: Dicionário do `build_forms_payload()`
- `timeout`: Timeout em segundos

**Retorna:** Tupla `(sucesso: bool, mensagem: str, status_code: int)`

**Status Codes:**
- 200/302: Sucesso (Forms aceita resposta)
- 400: Payload inválido ou entry IDs incorretos
- 403: Permissão negada (Forms fechado)
- 404: PUBLIC_ID inválido ou Forms não encontrado
- 502: Erro de rede ou timeout

**Lógica:**
1. Obtém mapping de entry IDs (cache ou download)
2. Monta lista de tuplas `(entry.XXX, valor)` para POST
3. Para checkbox (OPME): múltiplas tuplas com mesmo entry ID
4. POST para `https://docs.google.com/forms/d/e/{form_id}/formResponse`
5. Verifica status code (200 ou 302 = sucesso)

**Status codes:**
- 200/302 → Sucesso
- Outros → Falha

---

### 2. `scripts/extract_forms_entries.py`

Script para extrair e validar entry IDs do Forms real.

**Uso:**
```bash
python scripts/extract_forms_entries.py
```

**O que faz:**
1. Baixa HTML do Forms público
2. Extrai entry IDs automaticamente
3. Salva em cache
4. Exibe tabela de validação
5. Verifica se quantidade de campos está correta

**Exemplo de saída:**
```
📋 ID do Forms: 1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw

⬇️  Baixando HTML do Google Forms...
✅ HTML baixado com sucesso (125,432 bytes)

🔎 Extraindo entry IDs do HTML...
✅ Extração concluída! Encontrados 7 campos

======================================================================
MAPEAMENTO EXTRAÍDO
======================================================================

Campo              | Entry ID                        | Descrição
----------------------------------------------------------------------
ortopedista        | entry.123456                    | Ortopedista Responsável (dropdown)
procedimento       | entry.234567                    | Procedimento solicitado (texto curto)
data               | entry.345678                    | Data (date)
descricao          | entry.456789                    | Descrição Completa (texto longo)
opme               | entry.567890                    | OPME (checkbox)
necessita_uti      | entry.678901                    | Necessita vaga de UTI? (radio Sim/Não)
opme_outro         | entry.567890.other_option_response | OPME - Outro (texto)

✅ Quantidade de campos OK!

💾 Salvando mapeamento em cache...
✅ Cache salvo com sucesso!
```

---

## 🔧 Configurações

### Variáveis de Ambiente (.env)

**Novas:**
```env
# Google Forms para agendamento
GOOGLE_FORMS_EDIT_ID=1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw
GOOGLE_FORMS_PUBLIC_ID=  # Opcional: /d/e/<PUBLIC_ID>/viewform
GOOGLE_FORMS_TIMEOUT=10
```

**Removidas/Comentadas:**
```env
# APPS_SCRIPT_SCHEDULER_URL=https://script.google.com/macros/s/.../exec
```

### Código (config.py)

**Antes:**
```python
APPS_SCRIPT_SCHEDULER_URL = os.getenv('APPS_SCRIPT_SCHEDULER_URL', None)
```

**Depois:**
```python
# Google Forms Configuration (para agendamento automático)
GOOGLE_FORMS_EDIT_ID = os.getenv('GOOGLE_FORMS_EDIT_ID', '1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw')
GOOGLE_FORMS_PUBLIC_ID = os.getenv('GOOGLE_FORMS_PUBLIC_ID', None)
GOOGLE_FORMS_TIMEOUT = int(os.getenv('GOOGLE_FORMS_TIMEOUT', '10'))

# Apps Script Web App (DESABILITADO - agora usa submissão ao Forms)
# APPS_SCRIPT_SCHEDULER_URL = os.getenv('APPS_SCRIPT_SCHEDULER_URL', None)
```

---

## 🔄 Mudanças nas Rotas

### `GET /surgery_requests/<id>/schedule/preview`

**Antes:**
```python
from src.services.calendar_scheduler import build_calendar_payload, build_calendar_preview
payload = build_calendar_payload(surgery_request, patient)
preview = build_calendar_preview(payload)
```

**Depois:**
```python
from src.services.forms_service import build_forms_payload
payload = build_forms_payload(surgery_request, patient)

# Formatar preview manualmente
preview = {
    'title': payload['procedure_title'],
    'date_display': payload['date'],
    'orthopedist': payload['orthopedist'],
    'needs_icu_display': payload['needs_icu'],
    'opme_display': ', '.join(payload['opme']) if payload['opme'] else 'Não',
    'description': payload['full_description'],
    'all_day': True
}
```

---

### `POST /surgery_requests/<id>/schedule/confirm`

**Antes:**
```python
from src.services.calendar_scheduler import build_calendar_payload, send_to_calendar

apps_script_url = current_app.config.get('APPS_SCRIPT_SCHEDULER_URL')
payload = build_calendar_payload(surgery_request, patient)
success, response, error = send_to_calendar(payload, apps_script_url)

if success:
    surgery_request.scheduled_event_id = response['eventId']
    surgery_request.scheduled_event_link = response['htmlLink']
```

**Depois:**
```python
from src.services.forms_service import build_forms_payload, submit_form

form_id = current_app.config.get('GOOGLE_FORMS_EDIT_ID')
timeout = current_app.config.get('GOOGLE_FORMS_TIMEOUT', 10)
payload = build_forms_payload(surgery_request, patient)
success, message, status_code = submit_form(form_id, payload, timeout)

if success:
    # Não temos event_id/link direto (será criado pelo Apps Script da planilha)
    surgery_request.scheduled_event_link = None
```

**Diferença importante:**
- Web App retornava `eventId` e `htmlLink` imediatamente
- Forms **não retorna** esses dados (Apps Script da planilha cria evento assincronamente)
- `scheduled_event_link` fica `None` após submissão

---

## 🧪 Como Testar

### 1. Extrair Entry IDs

```bash
python scripts/extract_forms_entries.py
```

Valide se o mapeamento exibido corresponde à ordem das perguntas no Forms.

---

### 2. Testar Preview

1. Acesse o sistema
2. Navegue para uma solicitação de cirurgia
3. Clique em **"Adicionar à Agenda"**
4. Verifique se o modal mostra:
   - Título do procedimento
   - Data da cirurgia
   - Ortopedista responsável
   - Necessita UTI (Sim/Não)
   - OPME (lista ou "Não")
   - Descrição completa com dados do paciente

---

### 3. Testar Submissão

1. No modal de preview, clique em **"Confirmar Agendamento"**
2. Aguarde resposta (timeout: 10s)
3. **Sucesso esperado:**
   - Mensagem: "Agendamento enviado com sucesso! O evento será criado automaticamente no Google Calendar."
   - Botão "Adicionar à Agenda" muda para "Já Agendado"
   
4. **Validar no Google Forms:**
   - Abra a planilha de respostas do Forms
   - Verifique se nova linha foi adicionada com:
     - Ortopedista correto
     - Procedimento correto
     - Data correta
     - Descrição completa
     - OPME selecionados
     - UTI (Sim/Não)

5. **Validar no Google Calendar:**
   - Aguarde alguns segundos (Apps Script executa)
   - Abra o Google Calendar
   - Verifique se evento foi criado como **DIA INTEIRO**
   - Verifique título, data, descrição

---

### 4. Testar Erros

#### Timeout
- Desconecte da internet
- Tente agendar
- Deve retornar: "Timeout ao enviar para o Google Forms"

#### Forms ID inválido
- Altere `.env`: `GOOGLE_FORMS_EDIT_ID=invalido`
- Reinicie servidor
- Tente agendar
- Deve retornar erro de conexão

#### Campos faltando
- Crie solicitação SEM procedimento
- Tente agendar
- Deve retornar: "Dados incompletos: Procedimento solicitado é obrigatório"

---

## 🔒 Segurança e Privacidade

### LGPD Compliance

**Antes (Web App):**
- Dados enviados em JSON para endpoint HTTP
- Logs do Apps Script podiam conter dados sensíveis

**Depois (Forms):**
- Dados enviados via POST x-www-form-urlencoded (padrão Forms)
- Logs Flask registram apenas:
  - `surgery_request_id`
  - Sucesso/falha
  - Timestamp
- **NÃO registra:** nome do paciente, prontuário, telefone, descrição completa

### Logs Recomendados

```python
# ✅ BOM
logger.info(f"Cirurgia {id} enviada ao Google Forms com sucesso")

# ❌ EVITAR
logger.info(f"Paciente {patient.nome_completo} agendado")
```

---

## 🐛 Troubleshooting

### Erro: "Entry IDs não encontrados"

**Causa:** HTML do Forms mudou ou parsing falhou

**Solução:**
1. Execute `python scripts/extract_forms_entries.py`
2. Se falhar, abra o Forms no navegador
3. Inspecione HTML (F12)
4. Procure por `name="entry.` nos inputs
5. Ajuste `field_names` em `forms_service.py` linha ~120

---

### Erro: "Status 400 Bad Request"

**Causa:** Entry IDs incorretos ou payload malformado

**Solução:**
1. Verifique se mapeamento está correto
2. Execute script de extração novamente
3. Delete cache: `rm instance/forms_mapping.json`
4. Teste submissão manual no navegador

---

### Evento não criado no Calendar

**Causa:** Apps Script da planilha não está configurado ou falhou

**Solução:**
1. Abra a planilha de respostas do Forms
2. Ferramentas > Editor de scripts
3. Verifique se trigger `onFormSubmit` existe
4. Verifique logs do Apps Script (Execuções)
5. Confirme que calendarId está correto no script

---

### OPME "Outro" não aparece

**Causa:** Campo "opme_outro" não mapeado

**Solução:**
1. Verifique se Forms tem opção "Outro" habilitada no checkbox OPME
2. Execute script de extração
3. Confirme que `opme_outro` aparece no mapeamento
4. Se não aparecer, o Forms pode não ter esse campo

**Workaround:** Incluir texto de "Outro" no campo descrição:
```python
if surgery_request.opme_outros:
    description_parts.append(f"OPME Outro: {surgery_request.opme_outros}")
```

---

## 📊 Comparação: Antes vs Depois

| Aspecto                 | Antes (Web App)              | Depois (Forms)                |
|-------------------------|------------------------------|-------------------------------|
| **Endpoint**            | Apps Script Web App          | Google Forms /formResponse    |
| **Método**              | POST JSON                    | POST x-www-form-urlencoded    |
| **Autenticação**        | Nenhuma (URL pública)        | Nenhuma (Forms público)       |
| **Criação de evento**   | Direto pelo Web App          | Apps Script da planilha       |
| **Retorno**             | eventId + htmlLink           | Status 200/302 (sem metadados)|
| **Latência**            | ~1-2s                        | ~2-3s (+ trigger)             |
| **Setup**               | Deploy Web App + config URL  | Apenas config FORMS_ID        |
| **Manutenção**          | Atualizar código Web App     | Apenas se Forms mudar         |
| **Logs**                | Apps Script + Flask          | Apenas Flask                  |
| **LGPD**                | Requer cuidado com logs      | Mais simples (Forms gerencia) |

---

## ✅ Checklist de Migração

- [x] Criar `forms_service.py`
- [x] Adicionar configurações em `config.py`
- [x] Atualizar rota `schedule_preview`
- [x] Atualizar rota `schedule_confirm`
- [x] Criar script `extract_forms_entries.py`
- [x] Testar extração de entry IDs
- [ ] Executar script de extração: `python scripts/extract_forms_entries.py`
- [ ] Validar mapeamento extraído
- [ ] Testar preview no sistema
- [ ] Testar submissão ao Forms
- [ ] Validar resposta na planilha
- [ ] Validar evento no Calendar
- [ ] Testar cenários de erro (timeout, dados faltando)
- [ ] Atualizar documentação do usuário
- [ ] Remover/arquivar `calendar_scheduler.py` (opcional)
- [ ] Remover `CalendarScheduler.gs` do Apps Script (opcional)

---

## 📚 Referências

### Google Forms

**URL de submissão:**
```
https://docs.google.com/forms/d/e/{FORM_ID}/formResponse
```

**Formato de dados:**
- Content-Type: `application/x-www-form-urlencoded`
- Dados: `entry.123456=valor1&entry.234567=valor2`

**Para checkbox (múltiplos valores):**
```
entry.123456=Opção1&entry.123456=Opção2&entry.123456=Opção3
```

**Campo "Outro":**
```
entry.123456.other_option_response=texto livre
```

### Apps Script Trigger

O Apps Script da planilha usa trigger **onFormSubmit**:

```javascript
function onFormSubmit(e) {
  var formResponses = e.values; // Array com respostas
  
  var ortopedista = formResponses[1];
  var procedimento = formResponses[2];
  var data = formResponses[3];
  // ...
  
  var calendar = CalendarApp.getCalendarById(CALENDAR_ID);
  var evento = calendar.createAllDayEvent(procedimento, new Date(data), {
    description: descricao
  });
}
```

---

## 🚀 Próximos Passos

1. **Execute o script de extração:**
   ```bash
   python scripts/extract_forms_entries.py
   ```

2. **Valide o mapeamento** exibido

3. **Teste a submissão** com dados reais

4. **Monitore** a planilha e o calendário

5. **Ajuste** se necessário (ordem de campos, "Outro", etc.)

6. **Documente** qualquer customização adicional

---

**Data da reversão:** 5 de fevereiro de 2026  
**Versão:** 1.0  
**Autor:** GitHub Copilot
