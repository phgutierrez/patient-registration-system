# ❌→✅ Correção: Erros de Schema SQLite/SQLAlchemy

## 🔴 Problema

Ao usar o sistema, você pode estar recebendo erros como:

```
sqlite3.OperationalError: no such column: surgery_requests.scheduled_at
```

Ou ao criar solicitação:

```
(sqlite3.OperationalError) table surgery_requests has no column named scheduled_at
```

---

## 🔍 Causa

O model SQLAlchemy `SurgeryRequest` foi atualizado com novos campos de agendamento:

```python
scheduled_at = db.Column(db.DateTime, nullable=True)
scheduled_event_id = db.Column(db.String(255), nullable=True)
scheduled_event_link = db.Column(db.String(500), nullable=True)
calendar_status = db.Column(db.String(20), nullable=True)
```

Porém, **o banco de dados SQLite ainda não tem essas colunas** porque a migração não foi aplicada.

---

## ✅ Solução

### Opção 1: Migração Manual (Recomendado)

Execute no terminal:

```bash
# Ativar o ambiente virtual
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# ou
.\.venv\Scripts\activate.bat   # Windows CMD

# Executar a migração
alembic upgrade head
```

**Esperado:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume sqlite3 version ~3.7.0.
INFO  [alembic.runtime.migration] Running upgrade 001_create_calendar_cache -> add_calendar_fields, Running upgrade 001_create_calendar_cache -> add_calendar_fields, Add scheduling fields to surgery_requests
```

---

### Opção 2: Auto-Migração (Conveniente)

Se você quiser que a migração seja executada automaticamente:

```bash
# Ativar o ambiente virtual
.\.venv\Scripts\Activate.ps1

# Definir AUTO_MIGRATE=true e iniciar o servidor
$env:AUTO_MIGRATE='true'
python run.py
```

**O que acontece:**
1. ✅ Script detecta colunas faltando
2. ✅ Executa `alembic upgrade head` automaticamente
3. ✅ Servidor inicia normalmente

---

### Opção 3: Verificar Schema (Debug)

Para verificar o status da migração:

```bash
python scripts/check_and_migrate_schema.py
```

**Saída esperada (antes da migração):**
```
======================================================================
  VERIFICAÇÃO DE SCHEMA - CIRURGIA AGENDAMENTO
======================================================================

🔍 Verificando colunas de agendamento em surgery_requests...
  • scheduled_at: FALTANDO
  • scheduled_event_id: FALTANDO
  • scheduled_event_link: FALTANDO
  • calendar_status: FALTANDO

⚠️  4 coluna(s) faltando: scheduled_at, scheduled_event_id, scheduled_event_link, calendar_status

⚠️  AUTO_MIGRATE não está habilitado

  SOLUÇÃO: Execute a migração manualmente:

    alembic upgrade head
```

---

## 📋 Passo a Passo Completo

### 1. Abrir o Terminal

**Windows:**
- Pressione `Win + R`
- Digite: `powershell`
- Navegue para o projeto: `cd D:\Users\phgut\OneDrive\Documentos\patient-registration-system`

---

### 2. Ativar Ambiente Virtual

```bash
.\.venv\Scripts\Activate.ps1
```

Se receber erro de permissão, execute como Admin:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

---

### 3. Executar Migração

```bash
alembic upgrade head
```

Aguarde a mensagem de sucesso:
```
INFO  [alembic.migration] Running upgrade 001_create_calendar_cache -> add_calendar_fields
```

---

### 4. Verificar (Opcional)

```bash
python scripts/check_and_migrate_schema.py
```

**Saída esperada:**
```
======================================================================
  VERIFICAÇÃO DE SCHEMA - CIRURGIA AGENDAMENTO
======================================================================

🔍 Verificando colunas de agendamento em surgery_requests...
  • scheduled_at: OK
  • scheduled_event_id: OK
  • scheduled_event_link: OK
  • calendar_status: OK

✅ Schema está atualizado! Nenhuma migração necessária.

======================================================================
✅ SISTEMA PRONTO!
======================================================================
```

---

### 5. Iniciar o Sistema

```bash
python run.py
```

Agora o sistema deve funcionar sem erros!

---

## 🧪 Testar os Dois Cenários

### Cenário 1: Visualizar Paciente

1. Acesse `http://localhost:5000`
2. Login com um usuário
3. Clique em "Listar Pacientes"
4. Clique em um paciente
5. ✅ Deve abrir sem erro "no such column"

### Cenário 2: Criar Solicitação de Cirurgia

1. Abra um paciente
2. Clique em "Nova Solicitação de Cirurgia"
3. Preencha todos os campos
4. Clique em "Registrar"
5. ✅ Deve funcionar sem erro de INSERT

---

## 🐛 Troubleshooting

### Erro: "No module named 'alembic'"

```bash
pip install alembic
```

---

### Erro: "Can't find executable alembic"

Certifique-se que o ambiente virtual está ativado:

```bash
# Verificar
where python  # Deve mostrar caminho dentro de .venv

# Se não, ativar:
.\.venv\Scripts\Activate.ps1
```

---

### Erro: "FAILED: Target database is not up to date"

Às vezes o banco fica em estado inconsistente. Solução:

```bash
# 1. Verificar histórico de migrações
alembic history

# 2. Se necessário, fazer downgrade e upgrade novamente
alembic downgrade -1
alembic upgrade head
```

---

### Erro: "OperationalError: UNIQUE constraint failed"

Se houver conflito de migrações, execute:

```bash
# Ver estado atual
alembic current

# Se estiver fora de sincronismo
alembic stamp head  # Marca como atualizado
alembic upgrade head
```

---

## 📁 Arquivos Modificados

- ✅ `migrations/versions/add_calendar_scheduling_fields.py` - Corrigido `down_revision`
- ✅ `scripts/check_and_migrate_schema.py` - Novo script de verificação
- ✅ Este documento

---

## ♻️ Para Futuras Migrações

Se você adicionar mais campos a `SurgeryRequest` no futuro:

1. **Criar nova migration:**
   ```bash
   alembic revision -m "Add new fields to surgery_requests"
   ```

2. **Editar arquivo gerado em `migrations/versions/`:**
   ```python
   def upgrade():
       with op.batch_alter_table('surgery_requests', schema=None) as batch_op:
           batch_op.add_column(sa.Column('new_field', sa.String(100), nullable=True))
   
   def downgrade():
       with op.batch_alter_table('surgery_requests', schema=None) as batch_op:
           batch_op.drop_column('new_field')
   ```

3. **Aplicar:**
   ```bash
   alembic upgrade head
   ```

---

## ✅ Checklist

- [ ] Terminal aberto e ambiente virtual ativado
- [ ] Executou `alembic upgrade head` ou `AUTO_MIGRATE=true python run.py`
- [ ] Script check_and_migrate_schema.py passou
- [ ] Pode visualizar paciente sem erro
- [ ] Pode criar solicitação de cirurgia sem erro
- [ ] Sistema rodando em `http://localhost:5000`

---

## 📞 Ainda com dúvidas?

1. Verifique se está no diretório correto: `d:\Users\phgut\OneDrive\Documentos\patient-registration-system`
2. Verifique se o ambiente virtual está ativado (deve ter `(.venv)` no início do prompt)
3. Execute `python scripts/check_and_migrate_schema.py` para diagnóstico detalhado
4. Se ainda não funcionar, consulte os logs: `python run.py` e procure por mensagens de erro

---

**Criado:** 5 de fevereiro de 2026  
**Versão:** 1.0
