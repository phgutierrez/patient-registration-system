# PRD — Patient Registration System (v2)

**Produto:** Sistema Web de Registro de Pacientes + Solicitação/Agendamento Cirúrgico + PDFs

**Baseado em:** patient-registration-system (cadastro, cirurgias, PDFs, Google Forms)

**Versão do PRD:** 1.0

**Owner:** Dr. Pedro

**Usuários-alvo:** ambulatório / secretaria / equipe cirúrgica

---

## 1. Visão do Produto

Um sistema simples e confiável para:

- Cadastrar pacientes e manter dados essenciais
- Registrar solicitações cirúrgicas e acompanhar status
- Gerar PDFs padronizados (solicitação, documentos)
- Opcionalmente integrar com Google Forms como ponte rápida de fluxo
- Com foco em agilidade, padronização e rastreabilidade (quem fez o quê e quando)

---

## 2. Problema que Resolve

- **Perda de tempo com cadastro repetido** e informação espalhada (WhatsApp, papel, planilha)
- **Solicitação cirúrgica sem trilha clara:** "quem pediu?", "o que falta?", "em que status está?"
- **PDFs e formulários preenchidos na mão** → erro, retrabalho e inconsistência

---

## 3. Objetivos (o que é sucesso)

- Reduzir tempo de cadastro e solicitação em >50%
- 90% das solicitações geradas com PDF completo sem retrabalho
- Ter status e pendências claros por paciente (documentos, risco, autorização, OPME)

---

## 4. Não-Objetivos (para não inflar)

- Não é prontuário completo com evolução médica detalhada (por enquanto)
- Não vai substituir o sistema hospitalar oficial
- Não vai fazer faturamento/TISS agora (isso vira módulo futuro)

---

## 5. Personas

### Secretaria / Regulação
- Cria/atualiza pacientes, abre solicitação, acompanha pendências e status

### Cirurgião
- Revisa dados, define procedimento, prioridade, imprime/gera PDF, acompanha andamento

### Administrador (você ou alguém designado)
- Gerencia usuários, permissões, templates de PDF, campos e listas (ex.: tipos de cirurgia)

---

## 6. Jornada do Usuário (fluxos principais)

### Fluxo A — Cadastro rápido
1. Buscar paciente por nome/CPF/CNS
2. Se não existir → criar paciente
3. Salvar → já permitir "Nova Solicitação Cirúrgica"

### Fluxo B — Solicitação cirúrgica
1. Abrir paciente
2. "Nova solicitação"
3. Preencher: procedimento, lateralidade, diagnóstico, prioridade, observações, anexos
4. Salvar → status inicial "Rascunho" ou "Em análise"
5. Gerar PDF da solicitação (modelo padrão)
6. Marcar pendências (ex.: risco cirúrgico, exames, autorização, OPME)

### Fluxo C — Acompanhamento / pipeline
Lista de solicitações com filtros por:
- Status (rascunho / pendente docs / pronto p/ agendar / agendado / realizado / cancelado)
- Prioridade
- Período
- Cirurgião
- Hospital/unidade

### Fluxo D — Integração Forms (opcional)
- Botão "Enviar para Forms" (preenche link com parâmetros) ou "Registrar resposta do Forms"
- O sistema armazena o link/ID da submissão e status

---

## 7. Requisitos Funcionais (MVP)

### 7.1 Autenticação e perfis
- Login (email + senha)
- Perfis: admin, cirurgião, secretaria
- Controle de acesso por perfil (RBAC)

### 7.2 Pacientes
**Campos mínimos:**
- Nome completo*
- Data de nascimento
- Sexo
- Nome da mãe (opcional)
- CPF (opcional)
- CNS (opcional)
- Contato (telefone)
- Observações gerais

**Funções:**
- Criar / editar / visualizar
- Busca rápida (nome/CPF/CNS)
- Histórico de solicitações cirúrgicas do paciente

### 7.3 Solicitações cirúrgicas
**Campos mínimos:**
- Paciente (vinculado)
- Diagnóstico (texto)
- Procedimento (lista + texto livre)
- Lateralidade (D/E/Bilateral/NA)
- Prioridade (Baixa/Média/Alta/Urgente)
- Status (Rascunho, Pendente docs, Pronto, Agendado, Realizado, Cancelado)
- Data prevista (opcional)
- Observações
- Responsável pela solicitação (usuário logado)
- Checklist de pendências (multi-check)

**Funções:**
- Criar / editar / visualizar
- Linha do tempo (logs básicos por mudança de status)

### 7.4 PDFs
- Escolher template "Solicitação Cirúrgica Padrão"
- Gerar PDF com campos preenchidos
- Download do PDF
- (Importante) não depender de edição manual depois

### 7.5 Listas e filtros
- Lista de pacientes com busca
- Lista de solicitações com filtros (status, prioridade, período)
- Exportação CSV/XLSX (MVP pode ser CSV; XLSX em v1.1)

---

## 8. Requisitos Funcionais (pós-MVP / v1.1+)

- Anexos por solicitação (PDF de exames, risco, autorização) com limite e política de retenção
- Templates múltiplos (solicitação, internação, declaração)
- Integração Google Forms de verdade (capturar resposta via API)
- Dashboard (contagem por status, tempo médio até "Pronto")
- Etiquetas e "tags" (OPME, UTI, complexidade)

---

## 9. Requisitos Não-Funcionais

- **Performance:** lista de solicitações carregar em < 2s (padrão)
- **Disponibilidade:** 99% (se rodar em servidor estável)
- **Auditoria:** registrar alterações críticas (status, dados sensíveis)
- **LGPD:** mínimo necessário, controle de acesso, logs, política de retenção
- **Backup:** backup diário automático do banco (ou pelo menos export seguro)

---

## 10. Segurança e LGPD (obrigatório no PRD)

- Hash de senha (bcrypt/argon2)
- Sessão segura (cookie httpOnly, CSRF)
- Perfis e permissões por rota
- **Logs de auditoria** (quem alterou e quando) para:
  - Dados do paciente
  - Status da solicitação
  - Geração de PDFs

- **Dados sensíveis:** evitar expor em logs e URLs

**Se houver anexos:** definir:
- Armazenamento (local/S3)
- Criptografia em repouso (ideal)
- Tempo de retenção e limpeza automática

---

## 11. Modelo de Dados (alto nível)

```
User
  id, name, email, password_hash, role, created_at

Patient
  id, full_name, dob, sex, mother_name, cpf, cns, phone, notes, created_at, updated_at

SurgeryRequest
  id, patient_id, diagnosis, procedure, laterality, priority, status,
  expected_date, notes, created_by_user_id, created_at, updated_at

ChecklistItem
  id, surgery_request_id, item_key, label, is_done, done_at, done_by_user_id

AuditLog (mínimo)
  id, actor_user_id, entity_type, entity_id, action, diff_json, created_at
```

---

## 12. Páginas / Telas (escopo UI)

- **Login**
- **Dashboard** (MVP pode ser simples: cards por status)
- **Pacientes**
  - Lista + busca + botão "Novo"
- **Paciente (detalhe)**
  - Dados + histórico de solicitações
- **Solicitações**
  - Lista + filtros
- **Solicitação (detalhe/edição)**
  - Campos + checklist + botão "Gerar PDF"
- **Admin**
  - Usuários (criar, editar, desativar)
  - Listas (procedimentos, checklists padrão)
  - Templates PDF

---

## 13. Critérios de Aceitação (MVP)

- [ ] Consigo criar um paciente e encontrá-lo por busca
- [ ] Consigo criar uma solicitação vinculada e mudar status
- [ ] Consigo gerar um PDF preenchido e baixar
- [ ] Perfis bloqueiam acesso indevido (secretaria não acessa admin)
- [ ] Logs registram mudança de status com usuário e horário

---

## 14. Métricas (para você saber se tá bom)

- Tempo médio "cadastro+solicitação" (meta: cair pela metade)
- % solicitações com PDF gerado sem edição
- Tempo médio por status (pendente → pronto → agendado)

---

## 15. Riscos e Mitigação

| Risco | Mitigação |
|-------|-----------|
| Ambiente hospitalar instável / sem admin no Windows | Empacotar bem (exe/portable) + docs claros + backup simples |
| Dados sensíveis e LGPD | RBAC + logs + backups + evitar vazamento em exportações |
| Templates PDF quebrando por variação | Padronizar templates e manter versão por template |

---

## 16. Plano de Entrega (ideal para vibe coding)

### Sprint 0 (fundação)
Setup do projeto, banco, migrations, login, RBAC

### Sprint 1 (cadastro)
CRUD paciente + busca + página detalhe

### Sprint 2 (solicitação cirúrgica)
CRUD solicitação + status + filtros

### Sprint 3 (PDF)
Template 1 + geração + download

### Sprint 4 (admin + logs)
Usuários + audit log mínimo

### Sprint 5 (export)
CSV e/ou XLSX

---

## 17. Prompts Prontos para Vibe Coding

Você pode usar assim, sequencialmente:

### Prompt 1 — Setup
Crie um app Flask com SQLAlchemy + Alembic, autenticação (email/senha), RBAC (admin/cirurgiao/secretaria), Bootstrap no frontend, com estrutura src/, templates/, static/ e testes básicos.

### Prompt 2 — Pacientes
Implemente CRUD completo de Patient com busca por nome/CPF/CNS, validações, e página de detalhe mostrando dados e lista de solicitações vinculadas.

### Prompt 3 — Solicitações
Implemente CRUD de SurgeryRequest vinculado ao Patient, com status, prioridade, checklist de pendências, e página de lista com filtros e paginação.

### Prompt 4 — PDF
Implemente geração de PDF preenchido a partir de template (campos do paciente e solicitação). Botão "Gerar PDF" na tela da solicitação e download imediato.

### Prompt 5 — Auditoria
Implemente AuditLog para registrar mudanças de status e alterações em campos críticos, incluindo actor_user_id, entity_type, entity_id, diff_json e timestamp.

### Prompt 6 — Export
Implemente exportação CSV (e XLSX opcional) da lista de solicitações filtradas.

---

# Aditivo ao PRD — Agenda Google + Realizada/Suspensa (v1.1)

## 1. Objetivo

- Exibir, dentro do sistema, uma agenda cirúrgica integrada ao Google Agenda (preferencialmente via link público ICS)
- Permitir marcar cada solicitação como **Realizada** ou **Suspensa**, exigindo motivo da suspensão
- Registrar tudo em auditoria

---

## 2. Requisitos Funcionais Novos

### 2.1 Integração com Google Agenda (via link público / ICS)

#### Escopo (MVP dessa feature)

**Admin cadastra:** um ou mais calendários por unidade/serviço (ex.: "Centro Cirúrgico CPAM", "Escoliose CPAM")
- Nome
- url_ics_publica (link do Google Agenda em formato ICS)
- Timezone (padrão: America/Fortaleza)
- Ativo (sim/não)

**Tela "Agenda":**
- Visualização semanal/mensal (pode iniciar simples: lista por dia)
- Eventos do calendário exibidos com:
  - Título
  - Início/fim
  - Local
  - Descrição (se disponível)

**Atualização:**
- Cache local (para não depender de tempo real e não sobrecarregar)
- Revalidação a cada X minutos (ex.: 10–30 min)

#### Comportamento e limitações
- Somente leitura (pelo menos nessa fase)
- Se o calendário não estiver público ou o link quebrar:
  - Sistema mostra aviso "Calendário indisponível" e registra erro em log técnico
- Não expor a URL ICS em páginas públicas do sistema (mostrar só para admin)

#### Critérios de aceitação
- [ ] Admin cola o link ICS do Google Agenda e salva
- [ ] A tela "Agenda" mostra eventos coerentes com o Google Agenda (título e horários corretos)
- [ ] Eventos respeitam timezone

### 2.2 Check de cirurgia: Realizada vs Suspensa + motivo

#### Novo fluxo de status

O status atual evolui assim:

```
Rascunho
  ↓
Pendente docs
  ↓
Pronto para agendar
  ↓
Agendado
  ↓ ┌─────────────────┐
    │                 │
    ↓                 ↓
  Realizada       Suspensa
                      ↓
                  Cancelada (mantém, diferente de suspensa)
```

#### Regras de negócio (bem claras)

- Só pode marcar **Realizada** se já estiver **Agendado** (ou então pedir confirmação/justificativa administrativa)

**Ao marcar Suspensa:**
- Motivo é obrigatório
- Registrar:
  - Data/hora da suspensão
  - Usuário que marcou
  - (opcional) "Remarcar?" sim/não
  - (opcional) Nova data prevista

**Diferenciar:**
- **Suspensa** = ocorreu no dia/fluxo do agendamento, mas não aconteceu por algum motivo operacional/clínico
- **Cancelada** = retirada do plano (decisão definitiva ou descontinuidade)

#### Motivos padronizados (lista editável pelo admin)

Criar uma tabela/lista para "Motivos de suspensão", com opção "Outro (descrever)".

**Sugestões iniciais:**
- Falta de leito/UTI
- Falta de OPME/material
- Falta de hemoderivados
- Pendência de documentação/exames
- Condição clínica do paciente (intercorrência)
- Falta de anestesista/equipe
- Falta de sala/tempo cirúrgico
- Paciente não compareceu
- Problema administrativo/regulação
- Outro (campo obrigatório)

#### UI (tela da solicitação)

Na tela "Solicitação (detalhe)" quando status = Agendado:

**Botão "Marcar como Realizada"** (com 1 clique)

**Botão "Marcar como Suspensa"** → abre modal com:
- Motivo (dropdown)
- Se "Outro" → descrição obrigatória
- Observações
- Checkbox "Deseja remarcar?" (se sim, pede data prevista)

#### Auditoria (LGPD e rastreabilidade)

Registrar no AuditLog:
- Mudança de status
- Motivo e observações de suspensão
- Usuário e timestamp
- Diffs em JSON (sem dados sensíveis desnecessários)

#### Critérios de aceitação
- [ ] Consigo marcar "Realizada" com 1 clique e isso aparece na lista e no histórico
- [ ] Consigo marcar "Suspensa" e o sistema exige motivo
- [ ] A lista de solicitações permite filtrar por Suspensa e exportar
- [ ] Suspensões ficam auditadas com data/usuário

---

## 3. Modelo de Dados (incremento)

### Tabelas novas/alteradas

#### SurgeryRequest (alterações)
```
Adicionar:
  status inclui "SUSPENSA"
  suspended_at (datetime, nullable)
  suspended_by_user_id (nullable)
  suspension_reason_id (nullable)
  suspension_reason_text (nullable, obrigatório se reason = "Outro")
  reschedule_requested (bool, default false)
  reschedule_date (date/datetime, nullable)
```

#### SuspensionReason (nova)
```
  id
  label
  is_active
  sort_order
```

#### CalendarFeed (nova)
```
  id
  name
  ics_url
  timezone
  is_active
  created_at, updated_at
```

#### CalendarEventCache (opcional, recomendado)
```
  id
  calendar_feed_id
  event_uid
  title
  start_at
  end_at
  location
  description
  last_fetched_at
```

---

## 4. Tela "Agenda" (escopo UI)

**Menu lateral/topo:** Agenda

**Filtros:**
- Calendário (dropdown)
- Intervalo (semana/mês)

**Lista de eventos:**
- Data (header)
- Cards por evento (horário + título + local)

**(v1.2 opcional) Linkar evento a uma Solicitação:**
- Botão "Vincular a solicitação" (match manual)

---

## 5. Backlog (épicos → histórias) para vibe coding

### Épico A — Google Agenda (ICS)
- Admin: CRUD de CalendarFeed
- Service: fetch ICS + parse + normalizar timezone
- Cache de eventos + refresh por TTL
- UI: página Agenda (lista por dia + filtros)

### Épico B — Realizada/Suspensa
- Model: novos campos em SurgeryRequest + tabela SuspensionReason
- Admin: CRUD de motivos
- UI: botões Realizada/Suspensa + modal
- Regras de validação + AuditLog
- Filtro/export de suspensas

---

**Documento criado em:** 5 de fevereiro de 2026

**Status:** Versão 1.0 (PRD base para v2 do sistema)
