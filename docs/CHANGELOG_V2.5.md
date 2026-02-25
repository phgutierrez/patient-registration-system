# Changelog - v2.5

Data de lançamento: 2024

## 🎯 Foco Principal

Correção da ordem de migrações no setup e melhoria significativa na documentação de instalação e troubleshooting.

---

## ✅ Correções (Fixes)

### 🔴 Critical Fix - Especialidades Não Aparecem na Página Inicial

**Problema**:
Após executar `setup_windows.bat`, a página inicial não mostrava a lista de especialidades para seleção.

**Causa Raiz**:
As migrações do Alembic estavam sendo executadas APÓS a criação dos registros de especialidades. Como a tabela `specialties` não existia ainda, os registros não podiam ser inseridos.

**Solução**:
Reordenado o fluxo do setup para:
1. `create_tables_direct.py` - Cria schema inicial
2. **`alembic upgrade head`** - Aplica todas as migrações (cria tabelas que faltam)
3. Python initialization script - Cria registros de especialidades e usuários

**Commit**: `3cad067` - fix: corrige ordem de migracao no setup...

---

## 🚀 Novas Funcionalidades

### 📋 Scripts de Lote (Batch) Completamente Reescritos

#### `setup_windows.bat`
- ✅ Verificação rigorosa de Python 3.11+ com extração de versão major.minor
- ✅ Instruções automáticas para instalar via winget se Python não encontrado
- ✅ Reordenação crítica: migrações agora rodam ANTES da inicialização de dados
- ✅ Mensagens de erro padronizadas com `[OK]`, `[ERRO]`, `[AVISO]`
- ✅ Saída more verbosa com detalhes do que está sendo criado

Mudanças: 
- Linhas 191-210: Migrações agora com hard error (exit /b 1)
- Linhas 215-280: Python script com logging detalhado

#### `run_local.bat` - Totalmente Reescrito
- ✅ 3 verificações pré-voo (database, .env, venv)
- ✅ Mensagens claras de erro [ERRO]/[OK]
- ✅ Usa `SERVER_HOST=127.0.0.1` (localhost apenas)
- ✅ Usa `DESKTOP_MODE=true` (auto-desliga ao fechar navegador)
- ✅ Melhor formatação com mensagens de startup

#### `run_network.bat` - Totalmente Reescrito
- ✅ 3 verificações pré-voo (database, .env, venv)
- ✅ Detecção automática de IP local
- ✅ Usa `SERVER_HOST=0.0.0.0` (toda rede)
- ✅ Usa `DESKTOP_MODE=false` (persistente)
- ✅ Mostra tanto localhost quanto URLs de rede

#### `verify_setup.bat` - Script Novo
- ✅ Ferramenta de diagnóstico para verificar setup completo
- ✅ Lista todas as especialidades criadas
- ✅ Lista todos os usuários criados
- ✅ Mostra error se especialidades faltarem
- ✅ Sugere passos de remedação

---

## 📚 Documentação Nova

### `QUICK_START.md` (NOVO)
Guia rápido de instalação e execução em 3 passos para usuários que não querem ler 20 páginas.

Seções:
- Para Instalação (Windows)
- Para Executar o Sistema
- Credenciais Padrão
- Problemas Comuns com Soluções Rápidas
- Próximos Passos

### `TROUBLESHOOTING_ESPECIALIDADES.md` (NOVO)
Guia especificamente focado no problema de especialidades não aparecerem.

Seções:
- Causas Possíveis (3 cenários)
- Verificar Se Especialidades Existem
- Opções de Solução (3 abordagens diferentes)
- Scripts de Remedação Prontos para Copiar/Colar

### `README.md` - Atualizado
- ✅ Nova seção destacada apontando para QUICK_START.md
- ✅ Seção de Problemas na Primeira Execução com links de troubleshooting
- ✅ Melhor navegação para usuários novos

### `INSTALLATION_GUIDE.md` - Atualizações v2.5 (Anterior)
Já atualizado em commit anterior com:
- Seção 5.6: Configuração de Especialidades e Agendas
- Troubleshooting atualizado (10.4, 10.6)
- Referência a v2.5 no sumário

---

## 🔄 Mudanças Técnicas

### Arquitetura de Especialidades
- ✅ Cada especialidade tem seu próprio `agenda_url` no Google Calendar
- ✅ Removido cache global `GOOGLE_CALENDAR_ID`
- ✅ Route `/agenda` cria CalendarService individual por especialidade
- ✅ Não há compartilhamento de agenda entre especialidades

### Ordem de Inicialização Corrigida
```
Antes (ERRADO):
1. create_tables_direct.py
2. Criar especialidades (tabela não existe - FALHA)
3. alembic upgrade head

Depois (CORRETO):
1. create_tables_direct.py
2. alembic upgrade head           ← CRITICAL
3. Criar especialidades (tabela existe - SUCESSO)
```

### Padrão de Mensagens Padronizado
Todos os scripts agora usam o mesmo padrão:
```
[OK]      - Operação sucedida
[ERRO]    - Erro crítico (necessita ação)
[AVISO]   - Aviso (operação continuou)
```

---

## 📊 Commits Desta Versão

| Commit | Mensagem | Arquivo | Escopo |
|--------|----------|---------|--------|
| `c46a89f` | fix: carrega agenda especifica da especialidade selecionada | src/routes/main.py | Código |
| `55ece3d` | docs: atualiza installation guide com configuracao de especialidades | INSTALLATION_GUIDE.md | Docs |
| `0c2c8e2` | fix: reescreve setup_windows.bat com verificacao forçada de Python 3.11 | setup_windows.bat | Setup |
| `3cad067` | fix: corrige ordem de migracao no setup | setup_windows.bat, run_local.bat, run_network.bat, verify_setup.bat | Setup |
| `12b2b93` | docs: adiciona QUICK_START.md, TROUBLESHOOTING_ESPECIALIDADES.md | QUICK_START.md, TROUBLESHOOTING_ESPECIALIDADES.md, README.md | Docs |

---

## 🧪 Como Testar Esta Versão

### Teste 1: Setup Limpo
```bash
# 1. Deletar banco de dados antigo
del instance\prontuario.db

# 2. Rodar setup
setup_windows.bat

# 3. Verificar
verify_setup.bat
```

Esperado:
- Especialidades aparecem na output
- Usuários aparecem na output
- Status: OK

### Teste 2: Seleção de Especialidade
```bash
# 1. Rodar sistema
run_local.bat

# 2. Na página inicial:
# - Escolher "Cirurgia Pediatrica"
# - Clicar em Agenda
# 3. Na página inicial:
# - Escolher "Ortopedia"
# - Clicar em Agenda
```

Esperado:
- Cada especialidade show seu próprio calendário
- Sem compartilhamento entre especialidades

### Teste 3: LAN
```bash
# 1. Rodar em um computador
run_network.bat

# 2. Em outro computador, acessar:
# http://IP-DO-PRIMEIRO:5000

# 3. Fazer login e testar
```

Esperado:
- Sistema acessível de outro computador
- Tudo funciona normalmente

---

## ⚠️ Notas Importantes

### Breaking Changes
- ❌ Usuários com banco de dados antigo: DELETE `instance/prontuario.db` e reexecute setup
- ❌ Alembic agora obrigatório (antes era opcional)

### Requisitos Atualizados
- Python: **3.11+** (enforçado durante setup)
- alembic.ini: **Obrigatório** (arquivo deve existir)

### Compatibilidade
- Windows: ✅ Completo suporte
- Linux: ⚠️ Parcial (scripts batch não funcionam, use alembic manualmente)
- macOS: ⚠️ Parcial (scripts batch não funcionam, use alembic manualmente)

---

## 📋 Checklist para Deployment

- [ ] Testar setup_windows.bat do zero
- [ ] Redefinir especialidades com verify_setup.bat
- [ ] Testar seleção de especialidades individuais
- [ ] Testar agenda de cada especialidade
- [ ] Testar modo LAN com múltiplos computadores
- [ ] Verificar Google Calendar integration
- [ ] Verificar Google Forms integration
- [ ] Testar login de todos os usuários padrão

---

## 🎁 Bônus

### Novos Comandos por Atalho
- **Alt+N** - Novo registro de paciente
- **Alt+L** - Lista de pacientes
- **Alt+U** - Gerenciamento de usuários

### Novos Scripts
- `verify_setup.bat` - Diagnosticar setup
- `QUICK_START.md` - Instalação rápida (novo!)
- `TROUBLESHOOTING_ESPECIALIDADES.md` - Troubleshooting específico (novo!)

---

## 🔮 Roadmap - Próximas Versões

### v2.6 (Em Planejamento)
- [ ] Interface de gerenciamento de especialidades (GUI)
- [ ] Backup automático do banco
- [ ] Logs mais detalhados
- [ ] Authentication melhorada (não password em plain text)
- [ ] Suporte para Linux/Mac (scripts nativos)

### v3.0 (Longo Prazo)
- [ ] API REST completa
- [ ] Frontend moderna (React/Vue)
- [ ] Mobile app
- [ ] Multi-tenant support
- [ ] Advanced reporting

---

## 📞 Suporte

Se encontrar problemas:

1. Execute `verify_setup.bat` para diagnóstico
2. Leia [TROUBLESHOOTING_ESPECIALIDADES.md](TROUBLESHOOTING_ESPECIALIDADES.md)
3. Veja [QUICK_START.md](QUICK_START.md) para instalação
4. Consulte [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) para detalhes
5. Abra issue: https://github.com/seu-repo/issues

---

**Versão**: 2.5
**Data**: Dezembro 2024
**Status**: ✅ Pronto para Produção
