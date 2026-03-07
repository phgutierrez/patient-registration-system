# 📚 Índice de Documentação

Guia central da documentação do **Sistema de Registro de Pacientes e Gerenciamento de Cirurgias**.

---

## 🚀 Comece aqui

1. [QUICK_START.md](QUICK_START.md) — instalação e execução em poucos passos.
2. [Quick Start Linux TI (1 página)](QUICK_START.md#quick-start-linux-ti-1-página) — acesso direto para implantação Linux hospitalar.
3. [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) — implantação detalhada.
4. [COMANDOS_ESSENCIAIS.md](COMANDOS_ESSENCIAIS.md) — referência rápida de comandos.

---

## 📖 Documentação por tema

### Instalação e operação
- [QUICK_START.md](QUICK_START.md)
- [Quick Start Linux TI (1 página)](QUICK_START.md#quick-start-linux-ti-1-página)
- [LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md)
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- [COMANDOS_ESSENCIAIS.md](COMANDOS_ESSENCIAIS.md)

### Troubleshooting
- [TROUBLESHOOTING_ESPECIALIDADES.md](TROUBLESHOOTING_ESPECIALIDADES.md)
- [FIXO_BANCO_DE_DADOS.md](FIXO_BANCO_DE_DADOS.md)

### Google Calendar / Google Forms
- [AGENDAMENTO_AUTOMATICO.md](AGENDAMENTO_AUTOMATICO.md)
- [GUIA_FORMS.md](GUIA_FORMS.md)
- [REVERSAO_FORMS.md](REVERSAO_FORMS.md)

### Produto e histórico
- [CHANGELOG_V2.5.md](CHANGELOG_V2.5.md)
- [PRD.md](PRD.md)

---

## 🗂️ Arquivos principais na raiz

- `README.md`
- `setup_windows.bat`
- `run_local.bat`
- `run_network.bat`
- `verify_setup.bat`
- `build_exe_32bits.py`

---

## 🎯 Casos comuns

### Instalar rapidamente
1. [QUICK_START.md](QUICK_START.md)
2. `setup_windows.bat`
3. `run_local.bat`

### Implantar em rede LAN
1. [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
2. `setup_windows.bat`
3. `run_network.bat`

### Resolver problemas de especialidade/procedimentos
1. `verify_setup.bat`
2. [TROUBLESHOOTING_ESPECIALIDADES.md](TROUBLESHOOTING_ESPECIALIDADES.md)
3. `python setup_init_data.py`

### Gerar executável
1. [COMANDOS_ESSENCIAIS.md](COMANDOS_ESSENCIAIS.md)
2. `python build_exe_32bits.py`

---

## ✅ Atualizações recentes (março/2026)

- Seed do EXE alinhado ao setup completo.
- Usuários iniciais com especialidade vinculada.
- Procedimentos e códigos SUS de Ortopedia carregados no seed do EXE.
- Modelos da solicitação isolados por especialidade + usuário.
- Dependências de segurança atualizadas (`Flask`, `Werkzeug`, `waitress`, `requests`).

---

## 📌 Versão atual da documentação

- Versão: **v2.6**
- Última atualização: **março/2026**
