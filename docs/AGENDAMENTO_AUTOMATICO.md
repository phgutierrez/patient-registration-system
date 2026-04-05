# Agendamento Automático no Google Calendar

Este documento descreve como configurar e usar o sistema de agendamento automático de cirurgias no Google Calendar.

## 📋 Visão Geral

O sistema permite agendar cirurgias automaticamente no Google Calendar **sem abrir o Google Forms**, com uma etapa de **pré-visualização e confirmação** antes do envio.

### Fluxo de Funcionamento

1. Usuário clica em "Adicionar à Agenda" na tela de confirmação da solicitação de cirurgia
2. Sistema exibe modal com **pré-visualização** dos dados que serão agendados:
   - Título (procedimento solicitado)
   - Data (dia inteiro)
   - Descrição completa (dados do paciente + cirurgia + recursos)
   - Ortopedista responsável
   - Necessidade de UTI
   - OPME solicitados
3. Usuário revisa os dados e clica em "**Confirmar Agendamento**"
4. Sistema envia dados ao Apps Script Web App via POST
5. Apps Script cria evento ALL-DAY no Google Calendar
6. Sistema marca a solicitação como "agendada" e salva link do evento

## 🚀 Configuração Inicial

### 1. Deploy do Apps Script Web App

1. Acesse https://script.google.com
2. Crie um novo projeto (botão "+ Novo projeto")
3. Copie o código do arquivo `scripts/CalendarScheduler.gs` para o editor
4. **Implante como Web App:**
   - Clique em "Implantar" > "Nova implantação"
   - Tipo: **Aplicativo da Web**
   - Descrição: "Calendar Scheduler API"
   - Executar como: **Eu** (seu email com acesso ao calendário)
   - Quem tem acesso: **Qualquer pessoa** (ambiente controlado)
   - Clique em "Implantar"
5. **Copie a URL da implantação** (algo como: `https://script.google.com/macros/s/AKfycby.../exec`)
6. **Importante:** Ao atualizar o código, faça uma **nova versão** em "Gerenciar implantações"

### 2. Configurar Variáveis de Ambiente

Edite o arquivo `.env` na raiz do projeto e adicione:

```bash
# URL do Apps Script Web App (copiada no passo anterior)
APPS_SCRIPT_SCHEDULER_URL=https://script.google.com/macros/s/AKfycby.../exec

# ID do Google Calendar (já configurado anteriormente)
GOOGLE_CALENDAR_ID=seu-calendario@group.calendar.google.com

# Timezone (já configurado)
GOOGLE_CALENDAR_TZ=America/Fortaleza
```

### 3. Executar Migração do Banco de Dados

Adicione os campos de agendamento à tabela `surgery_requests`:

```bash
# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# Executar migração
alembic upgrade head
```

Ou execute manualmente via Python:

```python
.\.venv\Scripts\python.exe -c "
from src.app import create_app
from src.extensions import db

app = create_app()
with app.app_context():
    # Adicionar colunas manualmente
    db.engine.execute('ALTER TABLE surgery_requests ADD COLUMN scheduled_at DATETIME')
    db.engine.execute('ALTER TABLE surgery_requests ADD COLUMN scheduled_event_id VARCHAR(255)')
    db.engine.execute('ALTER TABLE surgery_requests ADD COLUMN scheduled_event_link VARCHAR(500)')
    db.engine.execute('ALTER TABLE surgery_requests ADD COLUMN calendar_status VARCHAR(20)')
    print('Campos adicionados com sucesso!')
"
```

### 4. Reiniciar Servidor Flask

```bash
.\.venv\Scripts\python.exe run.py
```

## 📖 Como Usar

### Para o Usuário Final

1. Cadastre um paciente e solicite uma cirurgia normalmente
2. Na tela de confirmação, clique em **"Adicionar à Agenda"**
3. Um modal abrirá com a **pré-visualização** do evento:
   - Revise os dados cuidadosamente
   - Verifique se a descrição está completa
4. Clique em **"Confirmar Agendamento"**
5. Aguarde a mensagem de sucesso
6. Opcionalmente, clique em **"Abrir Evento no Google Calendar"** para visualizar

### Indicadores de Status

- **Botão verde "Adicionar à Agenda"**: Ainda não agendado
- **Botão verde claro desabilitado "Já Agendado"**: Já foi agendado anteriormente
- **Alerta azul no modal**: Evento já foi agendado (mostra data/hora do agendamento)

## 🧪 Testes

### Teste Manual do Apps Script

1. Acesse a URL do Apps Script no navegador (método GET):
   ```
   https://script.google.com/macros/s/AKfycby.../exec
   ```
   Deve retornar JSON com `status: "ok"`

2. Teste via curl (método POST):
   ```bash
   curl -X POST "https://script.google.com/macros/s/AKfycby.../exec" \
     -H "Content-Type: application/json" \
     -d '{
       "calendarId": "seu-calendario@group.calendar.google.com",
       "title": "Teste - Cirurgia de Escoliose",
       "date": "2026-03-15",
       "description": "Teste de agendamento automático",
       "orthopedist": "Dr. Teste",
       "needs_icu": true
     }'
   ```

### Teste das Rotas Flask

```bash
# Preview
curl http://localhost:5000/surgery_requests/1/schedule/preview

# Confirm (requer sessão autenticada)
curl -X POST http://localhost:5000/surgery_requests/1/schedule/confirm \
  -H "Content-Type: application/json" \
  -b cookies.txt
```

### Testes Unitários

```bash
pytest tests/test_calendar_scheduler.py -v
```

## 🔧 Troubleshooting

### Erro: "Endpoint de agendamento não configurado"

**Causa:** `APPS_SCRIPT_SCHEDULER_URL` não está definido no `.env`

**Solução:** Adicione a variável no arquivo `.env` e reinicie o servidor

### Erro: "Calendário não encontrado"

**Causa:** `GOOGLE_CALENDAR_ID` incorreto ou Apps Script sem permissão

**Solução:** 
1. Verifique se o ID do calendário está correto
2. Certifique-se de que o Apps Script está rodando como "Eu" (sua conta)
3. Verifique se sua conta tem acesso ao calendário

### Erro: "Timeout" ao confirmar agendamento

**Causa:** Apps Script lento ou fora do ar

**Solução:**
1. Teste a URL do Apps Script diretamente no navegador
2. Aumente o timeout em `calendar_scheduler.py` (linha ~195): `timeout=60`
3. Verifique logs do Apps Script em "Execuções" no editor

### Modal não abre ou botão não responde

**Causa:** Erro de JavaScript ou Bootstrap não carregado

**Solução:**
1. Abra o Console do navegador (F12) e verifique erros
2. Verifique se Bootstrap 5 está sendo carregado em `base.html`
3. Limpe cache do navegador (Ctrl+Shift+R)

## 📊 Estrutura de Dados

### Payload Enviado ao Apps Script

```json
{
  "calendarId": "seu-calendario@group.calendar.google.com",
  "title": "Correção Cirúrgica de Escoliose",
  "date": "2026-03-15",
  "description": "📋 DADOS DO PACIENTE\nNome: João Silva\n...",
  "orthopedist": "Dr. Luiz Eduardo Portela",
  "opme": [],
  "opme_other": "Ilizarov Adulto, Caixa 3,5mm",
  "needs_icu": true
}
```

### Resposta do Apps Script (Sucesso)

```json
{
  "ok": true,
  "message": "Evento criado com sucesso",
  "eventId": "abc123xyz",
  "htmlLink": "https://www.google.com/calendar/event?eid=...",
  "title": "Correção Cirúrgica de Escoliose",
  "date": "2026-03-15"
}
```

### Campos Adicionados ao Modelo SurgeryRequest

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `scheduled_at` | DateTime | Data/hora em que foi agendado |
| `scheduled_event_id` | String(255) | ID do evento no Google Calendar |
| `scheduled_event_link` | String(500) | Link direto para o evento |
| `calendar_status` | String(20) | Status: 'agendado', 'erro', null |

## 🔐 Segurança e Privacidade

### Dados Sensíveis

- ✅ **Não são logados em texto plano:** Prontuário, telefone, descrição completa
- ✅ **Logs registram apenas:** ID da solicitação, sucesso/falha, tempo de requisição
- ✅ **Dados enviados apenas para:** Google Calendar (via Apps Script autenticado)

### Controle de Acesso

- Sistema sem autenticação pública (ambiente controlado)
- Apps Script roda como conta específica (definida no deploy)
- Apenas usuários logados podem agendar cirurgias

## 📝 Manutenção

### Atualizar Apps Script

1. Edite o código em https://script.google.com
2. Salve o projeto
3. Vá em "Implantar" > "Gerenciar implantações"
4. Clique em ⚙️ (engrenagem) na implantação ativa
5. "Nova versão"
6. Salve
7. **Não é necessário alterar a URL**

### Limpar Agendamentos Antigos

```python
from src.app import create_app
from src.extensions import db
from src.models import SurgeryRequest

app = create_app()
with app.app_context():
    # Resetar todos os agendamentos (use com cautela!)
    SurgeryRequest.query.update({
        'scheduled_at': None,
        'scheduled_event_id': None,
        'scheduled_event_link': None,
        'calendar_status': None
    })
    db.session.commit()
```

## 🆚 Comparação: Antigo vs Novo

| Aspecto | Google Forms (Antigo) | Agendamento Automático (Novo) |
|---------|----------------------|-------------------------------|
| Pré-visualização | ❌ Não | ✅ Sim (modal completo) |
| Confirmação | ❌ Não | ✅ Sim (dois cliques) |
| Feedback imediato | ❌ Não | ✅ Sim (sucesso/erro) |
| Link do evento | ❌ Não | ✅ Sim (após agendar) |
| Registro no sistema | ❌ Não | ✅ Sim (scheduled_at, etc.) |
| Prevenção duplicação | ❌ Não | ✅ Sim (checa se já agendado) |
| Tipo de evento | Dia inteiro | Dia inteiro (mantido) |

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do Flask: `run.py` (terminal)
2. Verifique os logs do Apps Script: https://script.google.com > seu projeto > "Execuções"
3. Consulte este README
