# Guia Rápido: Agendamento via Google Forms

## ⚡ Setup em 3 Passos

### 1️⃣ Extrair Entry IDs do Forms

```bash
python scripts/extract_forms_entries.py
```

**O que esperar:**
- ✅ Cache salvo em `instance/forms_mapping.json`
- 📊 Tabela com mapeamento de 6-7 campos
- ⚠️ Se menos de 6 campos, ajustar ordem em `forms_service.py`

---

### 2️⃣ Validar Mapeamento

Abra o Forms no navegador e compare a **ordem das perguntas**:

| # | Pergunta no Forms                | Campo Mapeado       |
|---|----------------------------------|---------------------|
| 1 | Ortopedista Responsável          | `ortopedista`       |
| 2 | Procedimento solicitado          | `procedimento`      |
| 3 | Data                             | `data`              |
| 4 | Descrição Completa               | `descricao`         |
| 5 | OPME (checkbox)                  | `opme`              |
| 6 | Necessita vaga de UTI?           | `necessita_uti`     |

Se a ordem estiver diferente, edite [forms_service.py](../src/services/forms_service.py#L120) linha 120:

```python
field_names = [
    "ortopedista",      # Pergunta 1
    "procedimento",     # Pergunta 2
    "data",             # Pergunta 3
    "descricao",        # Pergunta 4
    "opme",             # Pergunta 5
    "necessita_uti"     # Pergunta 6
]
```

---

### 3️⃣ Testar no Sistema

1. **Criar solicitação de cirurgia** (todos os campos obrigatórios)
2. **Clicar em "Adicionar à Agenda"**
3. **Verificar preview** (modal com dados)
4. **Confirmar agendamento**
5. **Validar:**
   - ✅ Mensagem: "Agendamento enviado com sucesso!"
   - ✅ Nova resposta na [planilha do Forms](https://docs.google.com/spreadsheets/d/...)
   - ✅ Evento criado no [Google Calendar](https://calendar.google.com)

---

## 🔧 Configurações (.env)

```env
# Obrigatório
GOOGLE_FORMS_EDIT_ID=SEU_ID_DE_EDICAO_DO_FORMS

# Opcional
GOOGLE_FORMS_TIMEOUT=10
```

---

## 🐛 Solução Rápida de Problemas

### "Entry IDs não encontrados"

```bash
# Deletar cache e extrair novamente
rm instance/forms_mapping.json
python scripts/extract_forms_entries.py
```

---

### Evento não aparece no Calendar

1. Abrir [planilha de respostas](https://docs.google.com/spreadsheets/d/...)
2. Verificar se resposta foi adicionada
3. Ferramentas > Editor de scripts > Executar `onFormSubmit` manualmente
4. Verificar logs de execução

---

### Timeout ao enviar

```env
# Aumentar timeout no .env
GOOGLE_FORMS_TIMEOUT=30
```

---

## 📚 Documentação Completa

[docs/REVERSAO_FORMS.md](REVERSAO_FORMS.md)

---

## ✅ Checklist de Validação

- [ ] Script de extração executado sem erros
- [ ] Mapeamento tem 6+ campos
- [ ] Ordem dos campos confere com Forms
- [ ] Preview mostra dados corretos
- [ ] Submissão retorna sucesso
- [ ] Resposta aparece na planilha
- [ ] Evento criado no Calendar como DIA INTEIRO
- [ ] Não é possível agendar duas vezes a mesma cirurgia

---

**🎯 Objetivo:** Substituir integração com Apps Script Web App por submissão direta ao Google Forms, mantendo preview + confirmação.

**✨ Benefício:** Aproveitar Apps Script onFormSubmit da planilha (já funciona), sem necessidade de endpoint Web App separado.
