# 📊 Migrações do Banco de Dados

Documentação sobre as migrações Alembic deste projeto.

---

## 🔄 Cadeia de Migrações

As migrações devem ser aplicadas na seguinte ordem:

```
004_add_calendar_scheduling_fields.py
    ↓
005_create_calendar_event_status.py
    ↓
006_add_conditional_get_support.py
    ↓
007_add_specialties.py
```

---

## 📋 Algumas Migrações

### 004 - Campos de Agendamento de Calendário

**O que faz:**
- Adiciona campos `scheduled_at` (datetime)
- Adiciona `scheduled_event_id` (string)
- Adiciona `scheduled_event_link` (string)
- Adiciona `calendar_status` (string)

**Tabela afetada:** `surgery_requests`

**Dependências:** Nenhuma (primeira migração)

---

### 005 - Criar Tabela de Status de Eventos

**O que faz:**
- Cria tabela `calendar_event_status` para rastreamento
- Armazena UID de eventos e status (REALIZADA/SUSPENSA)

**Tabela afetada:** `calendar_event_status` (criar)

**Dependências:** 004

---

### 006 - Suporte GET Condicional

**O que faz:**
- Adiciona ETag e Last-Modified para cache
- Otimiza requisições ao Google Calendar

**Tabela afetada:** `calendar_cache`

**Dependências:** 005

---

### 007 - Adicionar Especialidades

**O que faz:**
- Cria tabela `specialties` com nome, slug, is_active
- Adiciona FK em `users` e `surgery_requests`

**Tabelas afetadas:** 
- `specialties` (criar)
- `users` (adicionar foreign key)
- `surgery_requests` (adicionar foreign key)

**Dependências:** 006

---

## 🛑 Migrações Deletadas

As seguintes migrações foram removidas por serem duplicadas:
- `002_create_calendar_event_status.py` (duplicado com 005)
- `003_add_conditional_get_support.py` (duplicado com 006)
- `add_calendar_scheduling_fields.py` (duplicado com 004)

---

## ⚡ Como Executar

### Aplicar todas as migrações
```powershell
alembic upgrade head
```

### Aplicar até migração específica
```powershell
alembic upgrade 006_add_conditional_get_support
```

### Reverter última migração
```powershell
alembic downgrade -1
```

### Ver status
```powershell
alembic current
alembic history
```

---

## 🔧 Criar Nova Migração

```powershell
# 1. Fazer mudança no modelo
# (editar src/models/*)

# 2. Gerar script de migração
alembic revision --autogenerate -m "descrição da mudança"

# 3. Revisar arquivo gerado em versions/
# (verificar se está correto)

# 4. Aplicar
alembic upgrade head
```

---

## ⚠️ Importante

1. **Nunca delete linha de um arquivo .py** já existente na pasta `versions/`
2. **Sempre atualize** `down_revision` corretamente
3. **Execute** `alembic upgrade head` durante setup (ANTES de criar dados)
4. **Em produção**, teste migrações em dev first

---

## 📌 CRÍTICO para Setup

No script `setup_windows.bat`:

```bash
# Obrigatório executar ANTES de criar especialidades
alembic upgrade head

# DEPOIS criar dados
python script.py  # que faz os INSERT
```

Se a ordem estiver errada, especialidades não aparecerão!

---

**Status**: ✅ Todas as migrações válidas e testadas
**Versão**: v2.5
**Data**: Fevereiro 2026
