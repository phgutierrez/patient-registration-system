# Release 2.0 - Sistema de Registro de Pacientes

**Data de Release:** Fevereiro 25, 2026  
**Branch:** `cipe`  
**Status:** ✅ Estável para Produção

---

## 🎯 Visão Geral

**Release 2.0 é uma consolidação major com foco em:**
- ✨ Suporte multi-especialidades (Ortopedia + Cirurgia Pediátrica)
- 📚 Documentação reorganizada e completa
- 🔧 Correções críticas de agendamento
- 🏗️ Limpeza e otimização do projeto

---

## ✨ Principais Features (Novas em v2.0)

### 1. **Multi-Especialidades** ⭐
- Cada especialidade tem sua própria agenda Google Calendar
- Suporte para múltiplas especialidades (Ortopedia, Cirurgia Pediátrica, etc)
- Seleção de especialidade no início da sessão
- Agendas não compartilham cache (cada uma independente)

**Commits:**
- `abeff3e` - feat: suporte multi-especialidade
- `c46a89f` - fix: carrega agenda especifica da especialidade selecionada

### 2. **Documentação Reorganizada** 📚
- 7 arquivos `.md` movidos para pasta `docs/`
- Novo `docs/INDEX.md` com índice completo e busca por tópico
- `docs/README.md` como guia da pasta docs
- Documentação de migrations em `migrations/README.md`
- Guia rápido (`QUICK_START.md`) para instalação em 3 passos
- Troubleshooting especializado (`TROUBLESHOOTING_ESPECIALIDADES.md`)

**Commits:**
- `2c86e03` - refactor: agrupar documentacoes em docs/, remover build 64bits
- `cf88c83` - docs: adiciona INDEX.md

### 3. **Setup Corrigido** 🔧
- **CRÍTICO**: Ordem de migrações corrigida (migrations agora rodam ANTES da criação de dados)
- Verificação forçada de Python 3.11+
- Instruções winget se Python não encontrado
- Script `verify_setup.bat` para diagnóstico
- Mensagens de erro padronizadas `[OK]`, `[ERRO]`, `[AVISO]`

**Commits:**
- `3cad067` - fix: corrige ordem de migracao no setup
- `0c2c8e2` - fix: reescreve setup_windows.bat com verificacao forçada de Python 3.11

### 4. **Build 32bits Preparado** 🏗️
- Deletado build 64bits (não será mais mantido)
- `build_exe_32bits.py` com instruções detalhadas inline
- Pronto para compilar executável 32bits no Windows
- Documentação em `docs/COMANDOS_ESSENCIAIS.md`

**Commits:**
- `2c86e03` - refactor: remover build 64bits

### 5. **Limpeza do Projeto** 🧹
- Deletada pasta `tests/` (5 arquivos de teste sem CI/CD)
- Removido `test_fixes.py` e `pytest` de dependências
- `.pytest_cache` removido

**Commits:**
- `e7358eb` - chore: remove unused tests folder and dependencies

### 6. **Correções de Bugs** 🐛
- Parser ICS otimizado
- Busca de pacientes por prontuário otimizada para LAN
- Rastreamento de status de eventos de calendário
- GET condicional para cache (ETag, Last-Modified)

**Commits:**
- `f916566` - feat: Otimiza busca de pacientes
- `8d85a47` - feat: Adiciona tabela CalendarEventStatus

---

## 📊 Estatísticas da Release

| Métrica | Valor |
|---------|-------|
| Commits desde v1.0.4 | 17 |
| Arquivos alterados | 40+ |
| Documentação nova | 3 arquivos |
| Migrations corrigidas | 1 (cadeia 004→005→006→007) |
| Builds removidos | 64bits deletado |
| Testes removidos | 5 arquivos |
| Código linhas | ~2000+ |

---

## 🔧 Mudanças Técnicas

### Migrations
- ✅ `004_add_calendar_scheduling_fields.py` - Campos de agendamento
- ✅ `005_create_calendar_event_status.py` - Tabela de status
- ✅ `006_add_conditional_get_support.py` - Headers HTTP (ETag, Last-Modified)
- ✅ `007_add_specialties.py` - Tabelas de especialidades (corrigido down_revision)

### Estrutura de Pastas
```
Antes (v1.0.4):
- 7 arquivos .md na raiz
- build/, build_64bits/ (obsoletos)
- tests/ (sem CI/CD)

Depois (v2.0):
- docs/ (arquivos .md organizados)
- migrations/ com README
- Apenas build 32bits
- Sem pasta tests/
```

### Dependências
- Removido `pytest==7.4.3` (testes não mantidos)
- Mantido: Flask, SQLAlchemy, Waitress, ReportLab, etc
- Total: 22 pacotes

---

## ⚠️ Breaking Changes

**Nenhum breaking change para usuários finais!**

- ✅ Compatível com banco de dados v1.0.4
- ✅ Especialidades criadas automaticamente no setup
- ✅ Formulários Google Forms continuam funcionando
- ✅ Agendas Google Calendar continuam funcionando

---

## 🚀 Como Usar v2.0

### Windows - Instalação Rápida
```powershell
setup_windows.bat     # Instalação automática
verify_setup.bat      # Verificar se deu certo
run_local.bat         # Rodar localmente
# ou
run_network.bat       # Rodar em rede (hospital)
```

### Windows - Compilar Executável 32bits
```powershell
.\.venv32\Scripts\Activate.ps1
python build_exe_32bits.py
deactivate
# Resultado: dist\Sistema32bits\PatientRegistration\PatientRegistration.exe
```

### Documentação
- **Novo ao projeto?** → [docs/QUICK_START.md](docs/QUICK_START.md)
- **Instalação completa?** → [docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)
- **Problemas?** → [docs/TROUBLESHOOTING_ESPECIALIDADES.md](docs/TROUBLESHOOTING_ESPECIALIDADES.md)
- **Índice completo** → [docs/INDEX.md](docs/INDEX.md)

---

## 🐛 Bugs Corrigidos

| Bug | Solução | Commit |
|-----|---------|--------|
| Especialidades não aparecem após setup | Reordenar migrations antes da criação de dados | `3cad067` |
| Agenda Pediátrica mostrava Ortopedia | Remover cache compartilhado, usar por especialidade | `c46a89f` |
| Build 64bits confuso | Deletar e focar em 32bits only | `2c86e03` |
| Documentação espalhada | Centralizar em docs/ com índice | `2c86e03` |

---

## 📦 Requisitos

- **Python (geral)**: 3.11+ para setup padrão (`setup_windows.bat`)
- **Python (build EXE 32bits)**: 3.9.x 32-bit suportado e recomendado no fluxo legado de build
- **Windows**: 7, 8, 8.1, 10, 11 (32-bit e 64-bit)
- **Navegador**: Qualquer um moderno (Chrome, Firefox, Edge, Safari)
- **RAM**: Mínimo 2GB (recomendado 4GB)
- **Banco de Dados**: SQLite (incluído)
- **Conexão**: Opcional (Google Calendar/Forms requer internet)

---

## 🔄 Atualização de v1.0.4 → v2.0

### Backup (RECOMENDADO)
```powershell
# Fazer backup do banco antes de atualizar
Copy-Item "instance\prontuario.db" "instance\prontuario.db.backup"
```

### Atualizar
```powershell
# 1. Clone/pull nova versão
git pull origin cipe

# 2. Atualizar dependências
pip install -r requirements.txt

# 3. Aplicar migrations
alembic upgrade head

# 4. Testar
run_local.bat
```

### Esperar que aconteça
- ✅ Banco atualizado automaticamente (migrations)
- ✅ Especialidades criadas (se não existirem)
- ✅ Usuários mantidos (compatível)
- ✅ Agendas importadas automaticamente

---

## 📝 Créditos

**Desenvolvido por:** Pedro Freitas  
**Data:** Fevereiro 2026  
**Versão anterior:** v1.0.4  
**Status:** ✅ Production Ready

---

## 🔗 Links Importantes

- [GitHub Repository](https://github.com/phgutierrez/patient-registration-system)
- [Documentação Completa](docs/INDEX.md)
- [Guia Rápido](docs/QUICK_START.md)
- [Issues & Bug Reports](https://github.com/phgutierrez/patient-registration-system/issues)

---

## 📌 Nota de manutenção (Março/2026)

- Seed do EXE alinhado ao setup completo (especialidades, usuários e procedimentos de Ortopedia).
- Correção de usuários sem especialidade no fluxo do executável.
- Procedimentos e códigos SUS carregados corretamente por especialidade.
- Modelos de solicitação isolados por especialidade + usuário (sem cruzamento).
- Dependências de segurança atualizadas em `requirements.txt`.

---

## 📋 Próximas Prioridades (v2.1+)

- [ ] Interface de gerenciamento de especialidades (sem código)
- [ ] Backup automático de banco de dados
- [ ] Logs mais detalhados
- [ ] Melhorias de segurança
- [ ] API REST (v3.0)

---

**Status da Release:** ✅ **PRONTO PARA PRODUÇÃO**

Faça download, teste e compartilhe feedback!

---

**Última atualização:** Fevereiro 25, 2026
**Versão:** 2.0
**Hash:** cipe branch (v2.0 tag)
