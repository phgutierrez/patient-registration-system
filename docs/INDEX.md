# 📚 Índice de Documentação

Bem-vindo à documentação do **Sistema de Registro de Pacientes e Gerenciamento de Cirurgias**!

Este arquivo organiza toda a documentação disponível por categoria e caso de uso.

---

## 🚀 Para Começar

### Novo no projeto?
1. Leia [QUICK_START.md](QUICK_START.md) - Instalação em 3 passos
2. Veja [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Guia completo de configuração
3. Execute [Session Setup](../setup_windows.bat) (Windows) ou configure manualmente

### Problemas na instalação?
- Especialidades não aparecem → [TROUBLESHOOTING_ESPECIALIDADES.md](TROUBLESHOOTING_ESPECIALIDADES.md)
- Erros gerais → [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md#✅-troubleshooting)
- Comandos desconfigurados → [COMANDOS_ESSENCIAIS.md](COMANDOS_ESSENCIAIS.md)

---

## 📖 Documentação por Tópico

### Instalação e Setup
| Documento | Descrição | Para Quem |
|-----------|-----------|-----------|
| [QUICK_START.md](QUICK_START.md) | Guia ultra-rápido em 3 passos | Usuários finais |
| [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) | Guia completo e detalhado | Administradores |
| [COMANDOS_ESSENCIAIS.md](COMANDOS_ESSENCIAIS.md) | Referência de comandos Windows | Desenvolvedores |

### Solução de Problemas
| Documento | Descrição | Problema |
|-----------|-----------|----------|
| [TROUBLESHOOTING_ESPECIALIDADES.md](TROUBLESHOOTING_ESPECIALIDADES.md) | Especialidades/agendas não aparecem | Depois do setup |
| [FIXO_BANCO_DE_DADOS.md](FIXO_BANCO_DE_DADOS.md) | Problemas com banco de dados | Corrupção ou erro |
| [REVERSAO_FORMS.md](REVERSAO_FORMS.md) | Reverter formulário | Voltar configuração |

### Integração Google
| Documento | Descrição | Tópico |
|-----------|-----------|--------|
| [AGENDAMENTO_AUTOMATICO.md](AGENDAMENTO_AUTOMATICO.md) | Agendar cirurgias via Google Calendar | Google Calendar API |
| [GUIA_FORMS.md](GUIA_FORMS.md) | Integrar com Google Forms | Google Forms |
| [REVERSAO_RESUMO.md](REVERSAO_RESUMO.md) | Rollback de mudanças | Reversão |

### Referência Técnica
| Documento | Descrição | Para Quem |
|-----------|-----------|-----------|
| [CHANGELOG_V2.5.md](CHANGELOG_V2.5.md) | O que mudou na v2.5 | Desenvolvedores |
| [SESSION_SUMMARY.md](SESSION_SUMMARY.md) | Resumo da sessão de desenvolvimento | Equipe técnica |
| [PRD.md](PRD.md) | Product Requirements Document | Gerentes de projeto |

---

## 🗂️ Arquivos Raiz Principais

Na raiz do projeto você encontrará:
- **README.md** - Overview do projeto (SEMPRE LEIA PRIMEIRO!)
- **setup_windows.bat** - Script de instalação automática (Windows)
- **run_local.bat** - Executar localmente (PC único)
- **run_network.bat** - Executar em rede LAN (hospital)
- **verify_setup.bat** - Diagnosticar problemas de setup
- **build_exe_32bits.py** - Construir executável 32bits (Windows)

---

## 🎯 Casos de Uso Comuns

### "Quero instalar no meu computador"
```
1. Leia: QUICK_START.md
2. Execute: setup_windows.bat (Windows) 
   OU siga INSTALLATION_GUIDE.md (manual)
3. Teste: run_local.bat
```

### "Quero instalar no hospital/rede"
```
1. Leia: INSTALLATION_GUIDE.md (seção 🌐)
2. Execute: setup_windows.bat (server Windows)
3. Configure: Google Calendar
4. Execute: run_network.bat
5. Teste: http://IP:5000 de outro computador
```

### "Tenho erro na instalação"
```
1. Execute: verify_setup.bat (seu_Windows)
2. Leia: TROUBLESHOOTING_ESPECIALIDADES.md
3. Se não resolver, ver: INSTALLATION_GUIDE.md#troubleshooting
```

### "Quero compilar um executável .exe"
```
1. Leia: COMANDOS_ESSENCIAIS.md (parte 1)
2. Prepare: Python 32bits em C:\Python311_32\
3. Execute: python build_exe_32bits.py
4. Resultado: dist\Sistema32bits\PatientRegistration\PatientRegistration.exe
```

### "Quero integrar Google Calendar"
```
1. Leia: AGENDAMENTO_AUTOMATICO.md
2. Siga: Passos de configuração no INSTALLATION_GUIDE.md (seção 5.6)
3. Configure: Especialidades com agenda_url
```

### "Forma de voltar mudanças (reverter)"
```
1. Leia: REVERSAO_FORMS.md
2. Ou: REVERSAO_RESUMO.md (resumido)
```

---

## 📊 Estrutura de Documentação

```
docs/
├── 🚀 QUICK_START.md                      ← COMECE AQUI (novo usuário)
├── 📖 INSTALLATION_GUIDE.md               ← Guia completo
├── 🛠️ COMANDOS_ESSENCIAIS.md             ← Comandos Windows
├── ⚠️ TROUBLESHOOTING_ESPECIALIDADES.md  ← Problemas comuns
├── 📅 AGENDAMENTO_AUTOMATICO.md          ← Google Calendar
├── 📝 GUIA_FORMS.md                      ← Google Forms
├── 🔄 REVERSAO_FORMS.md                  ← Rollback
├── 📦 REVERSAO_RESUMO.md                 ← Summary
├── 🐛 FIXO_BANCO_DE_DADOS.md             ← DB issues
├── 📋 CHANGELOG_V2.5.md                  ← What's new
├── 👥 SESSION_SUMMARY.md                 ← Dev notes
└── 📄 PRD.md                             ← Requirements
```

---

## 🔍 Busca Rápida por Palavra-chave

### Python / Ambiente Virtual
→ COMANDOS_ESSENCIAIS.md

### Google (Calendar/Forms)
→ AGENDAMENTO_AUTOMATICO.md ou GUIA_FORMS.md

### Windows / Executável
→ COMANDOS_ESSENCIAIS.md ou QUICK_START.md

### Especialidades / Agendas
→ TROUBLESHOOTING_ESPECIALIDADES.md

### Banco de Dados
→ FIXO_BANCO_DE_DADOS.md

### Erros / Problemas
→ TROUBLESHOOTING_ESPECIALIDADES.md ou INSTALLATION_GUIDE.md

### Requerimentos / Design
→ PRD.md

---

## 📞 Precisa de Ajuda?

1. **Primeiro**: Procure no índice acima pelo tópico
2. **Depois**: Leia o guia recomendado
3. **Se persistir**: Execute `verify_setup.bat` e copie a output
4. **Final**: Abra uma issue no GitHub com output + qual doc você leu

---

## 📝 Convenções de Documentação

- 📖 **Guias completos**: Detalhe, exemplos, passo a passo
- ⚡ **Quick start**: Brevidade máxima, 3-5 passos
- 🔧 **Comandos**: PowerShell para Windows
- ⚠️ **Troubleshooting**: Problema → Causa → Solução
- 📊 **Referência**: Tabelas, índices, estrutura

---

## 🚀 Versão Atual

**v2.5** - Fevereiro 2026
- ✅ Setup corrigido (especialidades agora aparecem)
- ✅ Agendas por especialidade (sem cache compartilhado)
- ✅ Documentação reorganizada e expandida

---

## 📅 Status da Documentação

| Documento | Status | Última Atualização |
|-----------|--------|-------------------|
| QUICK_START.md | ✅ Completo | v2.5 |
| INSTALLATION_GUIDE.md | ✅ Completo | v2.5 |
| TROUBLESHOOTING_ESPECIALIDADES.md | ✅ Completo | v2.5 |
| COMANDOS_ESSENCIAIS.md | ✅ Completo | v2.5 |
| AGENDAMENTO_AUTOMATICO.md | ✅ Completo | v2.4 |
| GUIA_FORMS.md | ✅ Completo | v2.3 |
| PRD.md | ✅ Completo | v2.0 |

---

**Última atualização**: Fevereiro 2026
**Versão da Docs**: 2.5
**Mantido por**: Pedro Freitas
