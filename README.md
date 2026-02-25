# 🏥 Sistema de Registro de Pacientes e Gerenciamento de Cirurgias

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3.3-black?logo=flask&logoColor=white)
![Waitress](https://img.shields.io/badge/Server-Waitress-green?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Pronto%20para%20Produção-success)

Sistema abrangente de gerenciamento de pacientes e agendamento de cirurgias ortopédicas pediátricas com interface moderna, geração automática de PDFs e integração com Google Calendar.

[📥 Instalação](#-instalação) • [🌐 Configuração de Rede](#-implantação-em-rede-lan) • [📖 Guia](INSTALLATION_GUIDE.md) • [🔧 Configuração](#-configuração)

</div>

---

> ⚡ **Novo ao projeto?** Veja o [QUICK_START.md](QUICK_START.md) para instalação em 3 passos!

---

## 📋 Sobre

Este sistema otimiza o fluxo de trabalho hospitalar para gerenciar pacientes ortopédicos pediátricos e solicitações de cirurgia. Fornece uma solução completa para registro de pacientes, agendamento de cirurgias, integração de calendário e geração de documentos - projetado para ambientes hospitalares Windows.

### ✨ Características Principais

- 🏥 **Fluxo Hospitalar** - Gerenciamento completo de registro de pacientes e solicitações de cirurgia
- 📅 **Integração Google Calendar** - Sincronização em tempo real com atualização de 60 segundos
- 📄 **Geração Automática de PDFs** - Documentos de solicitação de cirurgia (ReportLab)
- 🌐 **Pronto para LAN** - Pronto para produção com servidor WSGI Waitress
- ⚡ **Cache Rápido** - Cache de calendário TTL de 60 segundos com GET condicional
- 🎯 **Agendamento Inteligente** - Integração Google Forms para eventos de calendário automatizados
- 📊 **Rastreamento de Eventos** - Gerenciamento de status de cirurgia (realizada/suspensa)
- 🔒 **Seguro** - Proteção CSRF e autenticação de usuário
- 💾 **Armazenamento Confiável** - Banco de dados SQLite com gerenciamento automático de esquema

---

## 🏗️ Arquitetura

### Stack Tecnológico
- **Backend**: Flask 2.3.3, SQLAlchemy, SQLite
- **Frontend**: Templates Jinja2, Bootstrap 5, CSS/JS modernos
- **Servidor**: Servidor WSGI Waitress (pronto para produção)
- **Integrações**: Google Calendar (ICS), Google Forms, parsing iCalendar
- **PDF**: ReportLab para geração de documentos
- **Cache**: Thread-safe em memória + persistência em banco de dados

### Modelos de Dados
```
Patient
├── Informações pessoais (nome, data nascimento, CNS, endereço)
├── Dados médicos (diagnóstico, código CID)
└── SurgeryRequest[]
    ├── Dados clínicos (sintomas, detalhes do procedimento)
    ├── Agendamento (data/hora, assistente, equipamentos)
    ├── Integração Google Calendar
    └── Dados para geração de PDF

CalendarCache (TTL 60s)
├── Dados feed ICS com ETag/Last-Modified
├── Eventos parseados por data
└── Rastreamento de status

CalendarEventStatus
├── Mapeamento UID de evento
├── Status: REALIZADA / SUSPENSA
└── Motivos de suspensão
```

### Estrutura do Projeto
```
src/
├── app.py              # Factory da aplicação Flask
├── config.py           # Configuração de ambiente
├── extensions.py       # SQLAlchemy, Flask-Login, CSRF
├── models/            
│   ├── patient.py      # Modelo de dados do paciente
│   ├── surgery_request.py  # Solicitações de cirurgia
│   ├── calendar_cache.py   # Cache de calendário
│   └── calendar_event_status.py  # Status do evento
├── routes/
│   ├── main.py         # Dashboard, calendário, endpoints de cache
│   ├── patients.py     # Gerenciamento de pacientes
│   ├── surgery.py      # Fluxo de solicitação de cirurgia
│   ├── auth.py         # Autenticação
│   └── lifecycle.py    # Heartbeat/shutdown (modo desktop)
├── services/
│   ├── calendar_service.py      # Parsing ICS
│   ├── calendar_cache_service.py # Cache thread-safe de 60s
│   ├── calendar_scheduler.py    # Integração Google Forms
│   ├── forms_service.py         # Submissão Forms
│   └── forms_mapping.py         # Mapeamento de campos
├── templates/         # Templates HTML Jinja2
└── static/           # CSS, JavaScript, PDFs gerados
```
---

## 🎯 Funcionalidades

### Gerenciamento de Pacientes
- ✅ Registro completo com dados pessoais, endereço e informações médicas
- ✅ Capacidades de busca e filtragem
- ✅ Edição e visualização de registros de pacientes
- ✅ Validação automática de dados (CNS, códigos CID, telefone)
- ✅ Cálculo de idade e gerenciamento de contatos

### Fluxo de Trabalho de Solicitação de Cirurgia
- ✅ Formulários completos de solicitação de cirurgia
- ✅ Geração automática de PDF com dados do paciente
- ✅ Rastreamento de histórico de cirurgias por paciente
- ✅ Confirmação de documentos e download
- ✅ **Agendamento Automatizado via Google Forms**
  - Visualização antes da submissão
  - Integração direta com Forms
  - Fluxo Apps Script → Google Calendar
  - Evento criado automaticamente no Google Calendar
  - Proteção contra duplicatas

### Integração de Calendário
- ✅ **Sincronização Google Calendar em tempo real** (atualização de 60 segundos)
- ✅ **Cache inteligente** com GET condicional (ETag/Last-Modified)
- ✅ **Gerenciamento de status de eventos** (realizada/suspensa)
- ✅ **Manipulação de fuso horário** para Brazil/Fortaleza
- ✅ Parsing e normalização de eventos de dia inteiro
- ✅ Atualização manual de cache e endpoints de status

### Gerenciamento de Usuários
- ✅ Cadastro de médicos/solicitantes
- ✅ Campos CNS e CRM
- ✅ Sistema de autenticação simples

### Recursos de Produção
- ✅ **Servidor WSGI Waitress** (pronto para produção Windows)
- ✅ **Implantação LAN** com binding 0.0.0.0
- ✅ **Modo desktop** com auto-desligamento (apenas localhost)
- ✅ **Operações thread-safe** para acesso multi-usuário
- ✅ **Proteção CSRF** e logging

### Interface do Sistema
- ✅ Dashboard com atalhos rápidos (Alt+N, Alt+L, Alt+U)
- ✅ Cards clicáveis para navegação intuitiva
- ✅ Logo institucional e identidade visual
- ✅ Controles de desligamento do sistema
- ✅ Mensagens de feedback em tempo real

---

## ⚡ Início Rápido

### 🖥️ Modo Desktop (Usuário Único)
```bash
# Configuração local rápida
run_local.bat
# Acesso: http://localhost:5000
# Auto-desligamento quando o navegador fechar
```

### 🌐 Implantação em Rede (LAN)
```bash
# Implantação hospitalar multi-usuário
run_network.bat
# Acesso do servidor: http://localhost:5000
# Acesso da rede: http://IP_DO_SERVIDOR:5000
```

### 📋 Configuração da Primeira Execução
1. Sistema cria 5 usuários padrão: `pedro`, `andre`, `brauner`, `savio`, `laecio`
2. Selecione um usuário para começar
3. Use a navegação do dashboard:
   - **Alt+N** - Novo registro de paciente
   - **Alt+L** - Lista de pacientes
   - **Alt+U** - Gerenciamento de usuários

### ⚠️ Problemas na Primeira Execução?
- **Especialidades não aparecem**: Ver [TROUBLESHOOTING_ESPECIALIDADES.md](TROUBLESHOOTING_ESPECIALIDADES.md)
- **Outros erros**: Execute `verify_setup.bat` para diagnóstico
- **Não consegue instalar**: Ver seção "[Instalação](#-instalação)" abaixo

---

## 📦 Instalação

### Opção 1: Executável Windows (Recomendado)
1. **Baixe** a versão mais recente: [PatientRegistration-windows.zip](../../releases)
2. **Extraia** a pasta `PatientRegistration` (377 MB com dependências)
3. **Execute** `PatientRegistration.exe`
4. Sistema abre automaticamente no navegador padrão

> 💡 **Importante**: Mantenha a estrutura completa de pastas. Não mova apenas o arquivo .exe!

### Opção 2: Instalação Python

```bash
# 1. Clone o repositório
git clone https://github.com/phgutierrez/patient-registration-system.git
cd patient-registration-system

# 2. Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Instale dependências
pip install -r requirements.txt

# 4. Execute o sistema
python run.py
```

> 📖 **Guia Detalhado**: Veja [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) para instruções completas de implantação hospitalar.

## 🌐 Implantação em Rede (LAN)

Para **implantação hospitalar multi-usuário**:

```bash
# Opção 1: Script automatizado (recomendado)
run_network.bat

# Opção 2: Configuração manual
set SERVER_HOST=0.0.0.0
set SERVER_PORT=5000
set DESKTOP_MODE=false
set FLASK_ENV=production
waitress-serve --listen=0.0.0.0:5000 wsgi:application
```

**Acesso na Rede:**
- **Servidor local**: http://localhost:5000
- **Outros computadores**: http://SEU_IP:5000 (ex: http://192.168.1.100:5000)

> ⚠️ **Firewall**: Permita a porta 5000 no Windows Firewall para redes privadas

### 🖥️ Implantação Local (Usuário Único)

Para **desktop de usuário único** com auto-desligamento:

```bash
# Opção 1: Script automatizado
run_local.bat

# Opção 2: Configuração manual  
set DESKTOP_MODE=true
set SERVER_HOST=127.0.0.1
waitress-serve --listen=127.0.0.1:5000 wsgi:application
```

### 🔧 Configuração do Windows Firewall (Modo Rede)

Para permitir acesso de outros computadores:

**Windows Firewall:**
```bash
# Permitir porta 5000 - Rede Privada
netsh advfirewall firewall add rule name="Patient Registration System" dir=in action=allow protocol=TCP localport=5000 profile=private
```

**Configuração Manual:**
1. Painel de Controle → Sistema e Segurança → Windows Firewall
2. Configurações Avançadas → Regras de Entrada
3. Nova Regra → Porta → TCP → Porta 5000 → Permitir → Perfil: Privado

---

## 🔧 Configuração

### Variáveis de Ambiente

Crie arquivo `.env` a partir do `.env.example` e configure:

```bash
# Configuração Flask
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=production
FLASK_DEBUG=0

# Configuração do Servidor
SERVER_HOST=0.0.0.0        # 127.0.0.1 para local, 0.0.0.0 para LAN
SERVER_PORT=5000
DESKTOP_MODE=false         # true para auto-desligamento, false para LAN

# Integração Google Calendar (Obrigatório)
GOOGLE_CALENDAR_ID=seu-calendario-id@group.calendar.google.com
GOOGLE_CALENDAR_TZ=America/Fortaleza
GOOGLE_CALENDAR_ICS_URL=https://calendar.google.com/calendar/ical/SEU_CALENDARIO.ics
CALENDAR_CACHE_TTL_SECONDS=60

# Integração Google Forms (Opcional - Pré-configurado)
# Por padrão, o sistema usa o formulário hospitalar integrado
# Sobrescreva apenas se usar formulário personalizado
GOOGLE_FORMS_PUBLIC_ID=seu-id-publico-do-formulario
GOOGLE_FORMS_VIEWFORM_URL=https://docs.google.com/forms/d/e/SEU_ID/viewform
GOOGLE_FORMS_TIMEOUT=10

# Banco de Dados (Opcional, padrão: instance/prontuario.db)
# SQLALCHEMY_DATABASE_URI=sqlite:///instance/prontuario.db

# Gerenciamento de Ciclo de Vida (Modo Desktop)
LIFECYCLE_TIMEOUT_SECONDS=30
LIFECYCLE_HEARTBEAT_SECONDS=5
```

### Opções de Configuração Principais

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `SECRET_KEY` | Chave de criptografia de sessão Flask | dev-key-123 | Sim |
| `SERVER_HOST` | Endereço de binding (127.0.0.1=local, 0.0.0.0=LAN) | 127.0.0.1 | Não |
| `DESKTOP_MODE` | Habilitar auto-desligamento ao fechar navegador | false | Não |
| `GOOGLE_CALENDAR_ID` | ID do Google Calendar para feed ICS | - | Sim |
| `CALENDAR_CACHE_TTL_SECONDS` | Intervalo de atualização do calendário | 60 | Não |
| `GOOGLE_FORMS_PUBLIC_ID` | ID público do formulário para agendamento | - | Opcional |

---

## 💾 Banco de Dados e Migrações

### Configuração do Banco de Dados
```bash
# O sistema usa criação direta de tabelas (sem migrações necessárias)
# Arquivo do banco: instance/prontuario.db

# Verificar criação do banco
python -c "from src.app import create_app; app=create_app(); print('Banco de dados pronto!')"
```

### Estratégia de Backup
```bash
# Backup do banco SQLite
copy instance\prontuario.db instance\prontuario_backup_YYYY-MM-DD.db

# Restaurar do backup
copy instance\prontuario_backup_YYYY-MM-DD.db instance\prontuario.db
```

---

## 📅 Integração de Calendário

### Configuração do Google Calendar
1. **Crie ou Acesse** o Google Calendar
2. **Obtenha o ID do Calendário** em Configurações do Calendário → Integrar Calendário
3. **Obtenha a URL ICS**: `https://calendar.google.com/calendar/ical/ID_DO_CALENDARIO/public/basic.ics`
4. **Defina o fuso horário** para `America/Fortaleza`

### Comportamento do Cache
- **TTL**: 60 segundos (configurável)
- **Método**: GET condicional com ETag/Last-Modified
- **Fallback**: Serve cache antigo em erros de rede
- **Thread-safe**: Suporta múltiplos usuários

### Controle Manual do Cache
- **Atualizar**: POST `/agenda/cache/refresh`
- **Status**: GET `/agenda/cache/info`
- **Interface**: Disponível na interface do calendário

## 🚨 Solução de Problemas

### Problemas Comuns

**1. Aparece "Development server warning"**
```bash 
# Problema: Ainda usando servidor de desenvolvimento do Flask
# Solução: Use Waitress para produção
waitress-serve --listen=0.0.0.0:5000 wsgi:application
```

**2. Erros de banco "No such column"**
```bash
# Problema: Esquema do banco de dados desatualizado
# Solução: Recriar banco de dados
python create_tables_direct.py
```

**3. Datas do calendário com diferença de um dia**
```bash
# Problema: Parsing de fuso horário para eventos de dia inteiro
# Solução: Eventos são criados como dia inteiro no Google Calendar
# Este é o comportamento esperado para agendamento de cirurgias
```

**4. Erros 500 de rede de outros PCs**
```bash
# Problema: URLs localhost hardcoded ou firewall
# Solução:
# 1. Verificar SERVER_HOST=0.0.0.0 no .env
# 2. Permitir porta 5000 no Windows Firewall (redes privadas)
# 3. Verificar endereço IP real: ipconfig
```

**5. Erros 404/403 do Google Forms**
```bash
# Problema: ID ou URL do Forms incorretos
# Solução:
# - Use ID PÚBLICO do forms de /d/e/<ID_PUBLICO>/viewform
# - NÃO o ID de edição de /forms/d/<ID_EDICAO>/edit
# - Definir GOOGLE_FORMS_PUBLIC_ID no .env
```

**6. Erro "Port already in use"**
```bash
# Problema: Servidor anterior ainda em execução
# Solução:
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

**7. Calendário não atualizando**
```bash
# Problema: Cache não está atualizando
# Solução:
# - Verificar CALENDAR_CACHE_TTL_SECONDS=60 no .env
# - Atualização manual: POST /agenda/cache/refresh
# - Verificar se URL ICS está acessível
```

**8. Erros de banco de dados bloqueado**
```bash
# Problema: Múltiplos processos acessando SQLite
# Solução:
# 1. Parar todas as instâncias do servidor
# 2. Reiniciar uma vez com servidor WSGI correto
# 3. Usar apenas um processo de servidor para SQLite
```

---

## 📊 Status Atual & Roadmap

### ✅ Funcionalidades Prontas para Produção
- Registro e gerenciamento de pacientes
- Fluxo de solicitação de cirurgia com geração de PDF
- Integração Google Calendar com cache de 60 segundos
- Agendamento automatizado via Google Forms
- Rastreamento de status de eventos (realizada/suspensa)
- Implantação LAN com Waitress
- Suporte multi-usuário com autenticação básica

### ⚠️ Limitações Conhecidas
- **Sem autenticação avançada** - Sistema simples de seleção de usuário
- **Sem logs de auditoria** - Rastreamento limitado de atividades
- **Banco único** - Apenas SQLite (sem PostgreSQL/MySQL)
- **Sem permissões de usuário** - Todos os usuários têm acesso completo
- **Sem backup automatizado** - Backup manual necessário
- **Viés para português brasileiro** - Alguns formulários/validações para o Brasil

### 🔮 Roadmap
- [ ] Controle de acesso baseado em papéis (Admin/Médico/Enfermeiro)
- [ ] Logs de auditoria abrangentes
- [ ] Suporte PostgreSQL para implantações maiores
- [ ] Integração LDAP/Active Directory
- [ ] Agendamento de backup automatizado
- [ ] Suporte multi-idioma (Inglês/Espanhol)
- [ ] API REST para integrações
- [ ] Containerização Docker

### 🏥 Status de Implantação Hospitalar
- ✅ **Windows Server pronto** - Testado no Windows 10/11/Server
- ✅ **Otimizado para LAN** - Binding 0.0.0.0 com instruções de firewall
- ✅ **Servidor de produção** - Waitress WSGI (sem servidor de desenvolvimento)
- ✅ **Eficiente em recursos** - <50MB RAM, uso mínimo de CPU
- ✅ **Persistência de dados** - SQLite com segurança de transação
- ⚠️ **Backup obrigatório** - Backup manual do banco necessário
- ⚠️ **Servidor único** - Sem clustering/alta disponibilidade

---

## 📖 Documentação Adicional

- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Guia completo de implantação hospitalar
- **[.env.example](.env.example)** - Modelo de configuração com todas as variáveis
- **[Requirements](requirements.txt)** - Dependências Python com versões

---

## 📄 Licença

Licença MIT - Veja [LICENSE](LICENSE) para detalhes.

---

## 👨‍⚕️ Autor

**Dr. Pedro Henrique Freitas**
- Sistema desenvolvido para otimização do fluxo de trabalho em Ortopedia Pediátrica
- © 2026 - Todos os direitos reservados

---

## 📞 Suporte

Para relatar bugs ou solicitar recursos, abra uma [Issue](../../issues).

---

<div align="center">

**Desenvolvido com ❤️ para Ortopedia Pediátrica**

[⬆ Voltar ao topo](#-sistema-de-registro-de-pacientes--gerenciamento-de-cirurgias)

</div>