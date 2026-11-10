# 🏥 Sistema de Registro de Pacientes e Gerenciamento de Cirurgias

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1.3-black?logo=flask&logoColor=white)
![Waitress](https://img.shields.io/badge/Server-Waitress-green?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Pronto%20para%20Produção-success)

Sistema abrangente de gerenciamento de pacientes e agendamento de cirurgias ortopédicas com interface moderna, geração automática de PDFs e integração com Google Calendar.

[📥 Instalação](#-instalação) • [🌐 Configuração de Rede](#-implantação-em-rede-lan) • [📖 Documentação](docs/INDEX.md) • [🔧 Configuração](#-configuração)

</div>

---

> 📚 **Documentação Completa**: [Índice de Documentação](docs/INDEX.md) com busca por tópico
>
> ⚡ **Novo ao projeto?** Veja o [QUICK_START.md](docs/QUICK_START.md) para instalação em 3 passos!
>
> 🔐 **Segurança**: veja o pacote em [docs/security/README.md](docs/security/README.md)

---

## 📋 Sobre

Este sistema otimiza o fluxo de trabalho hospitalar para gerenciar pacientes ortopédicos e solicitações de cirurgia. Fornece uma solução completa para registro de pacientes, agendamento de cirurgias, integração de calendário e geração de documentos - projetado para ambientes hospitalares Windows.

### ✨ Características Principais

- 🏥 **Fluxo Hospitalar** - Gerenciamento completo de registro de pacientes e solicitações de cirurgia
- 📅 **Integração Google Calendar** - Sincronização em tempo real com atualização de 60 segundos
- 📄 **Geração Automática de PDFs** - Documentos finalizados no backend com PyMuPDF
- 🌐 **Multiestação offline-first** - SQLite privado por computador e sincronização criptografada pela pasta compartilhada
- ⚡ **Cache Rápido** - Cache de calendário TTL de 60 segundos com GET condicional
- 🎯 **Agendamento Inteligente** - Integração Google Forms para eventos de calendário automatizados
- 📊 **Rastreamento de Eventos** - Gerenciamento de status de cirurgia (realizada/suspensa)
- 🔒 **Seguro** - Proteção CSRF e autenticação de usuário
- 💾 **Armazenamento Confiável** - SQLite local, outbox transacional, checkpoints e histórico restaurável

### 🆕 Versão 2.7.0 (Novembro/2026)

- ✅ PDF de internação: faixa verde **RESERVAR VAGA DE UTI** no Aviso de Cirurgia quando há reserva de UTI
- ✅ Requisição de hemocomponente sempre com a **data de internação** (sem a data de exemplo 03/05/2024)
- ✅ Pacientes e Agenda atualizam só a área necessária (HTMX), sem recarregar a página
- ✅ Bundles locais com Vite, Alpine.js (CSP) e ícones Lucide; sem CDN e sem scripts inline
- ✅ Botão de menu visível em telas pequenas; `Werkzeug 3.1.9` (CVE-2026-102598)
- 📘 **Como atualizar (rede, EXE local, Python):** [docs/ATUALIZACAO_V2.7.md](docs/ATUALIZACAO_V2.7.md) · [Notas de versão](RELEASE_NOTES_2.7.md)

### Atualizações anteriores (Julho/2026)

- ✅ Seed do executável alinhado ao setup completo (especialidades + usuários + procedimentos)
- ✅ Usuários iniciais do EXE vinculados à especialidade (evita ortopedista sem especialidade)
- ✅ Procedimentos e códigos SUS carregados corretamente por especialidade
- ✅ Modelos de solicitação isolados por especialidade + usuário (sem carregamento cruzado)
- ✅ Dependências de segurança atualizadas (`Flask`, `Werkzeug`, `waitress`, `requests`)

---

## 🏗️ Arquitetura

### Stack Tecnológico
- **Backend**: Flask 3.1.3, SQLAlchemy, SQLite
- **Frontend**: Templates Jinja2, Bootstrap 5, HTMX + Alpine.js (build CSP) e ícones Lucide empacotados com Vite em `src/static/dist` — tudo local, sem CDN ([docs/FRONTEND.md](docs/FRONTEND.md))
- **Servidor**: Servidor WSGI Waitress (pronto para produção)
- **Integrações**: Google Calendar (ICS), Google Forms, parsing iCalendar
- **PDF**: PyMuPDF para preenchimento e incorporação permanente de formulários
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

CalendarCache (TTL padrão 300s)
├── Dados feed ICS com ETag/Last-Modified
├── Eventos parseados por data
└── Rastreamento de status

CalendarEventStatus
├── Mapeamento UID de evento
├── Status: PENDENTE / REALIZADA / SUSPENSA
├── Motivo opcional de suspensão
└── Vínculo seguro com SurgeryRequest quando identificável
```

### Interfaces operacionais

- A página inicial usa somente o SQLite local para contadores e próximos procedimentos.
- A lista de pacientes mantém busca e paginação no servidor, priorizando prontuário exato.
- O detalhe do paciente reúne os dados clínicos e o histórico cirúrgico; cada solicitação abre diretamente sua confirmação para revisão, edição, PDFs e eventual envio à agenda.
- Todos os médicos da Ortopedia podem consultar, acrescentar e corrigir procedimentos e códigos SUS. Integrações, ativação e exclusão permanecem administrativas.
- A solicitação permanece em uma única página e os modelos locais contêm apenas dados clínicos reutilizáveis.
- A agenda guarda uma cópia por especialidade. Dados expirados são exibidos imediatamente enquanto uma única atualização ocorre em segundo plano.
- O modal da agenda registra `Pendente`, `Realizada` ou `Suspensa` sem recarregar a página. Quando o evento contém uma referência segura, o status da solicitação é atualizado na mesma transação.
- Bootstrap, Font Awesome, CSS e JavaScript são servidos localmente e incluídos no executável.

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
│   └── specialty_settings.py # Configuração exclusiva de Ortopedia
├── services/
│   ├── calendar_service.py      # Parsing ICS
│   ├── calendar_cache_service.py # Cache por especialidade, persistente e thread-safe
│   ├── calendar_scheduler.py    # Integração Google Forms
│   ├── forms_service.py         # Submissão Forms
│   └── forms_mapping.py         # Mapeamento de campos
├── templates/         # Templates HTML Jinja2
└── static/           # CSS, JavaScript e ativos públicos
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
  - Fluxo Google Forms → automação externa do calendário
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
- ✅ Autenticação com PIN, troca obrigatória na primeira entrada e escopo por especialidade
- ✅ Autogestão de nome, CNS, CRM e PIN em **Meu Perfil**

### Recursos de Produção
- ✅ **Servidor WSGI Waitress** (pronto para produção Windows)
- ✅ **Implantação LAN** com binding 0.0.0.0
- ✅ **Modo desktop** com encerramento manual protegido (apenas localhost)
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
# O processo permanece ativo até clicar em "Encerrar sistema"
```

### 🌐 Implantação em Rede (LAN)
```bash
# Implantação hospitalar multi-usuário
run_network.bat
# Acesso do servidor: http://localhost:5000
# Acesso da rede: http://IP_DO_SERVIDOR:5000
```

### 📋 Configuração da Primeira Execução
1. Copie `.env.example` para `.env` se necessário
2. Inicie o sistema com `run_local.bat`
3. Se não houver usuários, crie o primeiro administrador pelo assistente aberto em `localhost`
4. Como alternativa automatizada, configure `ADMIN_BOOTSTRAP_USERNAME` e `ADMIN_BOOTSTRAP_PASSWORD`
5. Use a navegação do dashboard:
   - **Alt+N** - Novo registro de paciente
   - **Alt+L** - Lista de pacientes
   - **Alt+U** - Gerenciamento de usuários

### ⚠️ Problemas na Primeira Execução?
- **Especialidades não aparecem**: Ver [TROUBLESHOOTING_ESPECIALIDADES.md](docs/TROUBLESHOOTING_ESPECIALIDADES.md)
- **Outros erros**: Execute `verify_setup.bat` para diagnóstico
- **Não consegue instalar**: Ver seção "[Instalação](#-instalação)" abaixo

---

## 📦 Instalação

### Opção 1: Executável Windows (Recomendado)
1. **Baixe** a versão mais recente: [PatientRegistration-windows.zip](../../releases)
2. **Extraia** a pasta `PatientRegistration` com todas as dependências
3. **Execute** `PatientRegistration.exe`
4. Sistema abre automaticamente no navegador padrão

### Build do executável Windows 32-bit

Execute `build_exe_32bits.bat` na raiz do projeto. O build exige CPython 3.11
32-bit, que pode ser instalado somente para o usuário, e não requer Visual C++
Build Tools nem privilégios administrativos. O wheel win32 do `greenlet` fica
em `build_support/`, tem seu SHA-256 verificado e as demais dependências são
instaladas somente quando existe pacote binário compatível.

Os bundles do frontend (`src/static/dist`) são versionados no repositório, então o
build **não precisa de Node.js**. O script valida os manifestos do Vite antes do
build e confere os arquivos dentro de `_internal` depois. Quem alterar CSS/JS
deve rodar `npm ci && npm run build` (Node.js 20+) e versionar `src/static/dist`
(veja [docs/FRONTEND.md](docs/FRONTEND.md)).

O caminho exato do executável gerado é exibido ao final. Se a distribuição
anterior estiver aberta, o build cria uma nova pasta em `dist/` sem tentar
sobrescrever o processo em uso.

Na área administrativa em **Configurações → Banco Access de Pacientes**, a
origem da consulta pode ser definida como arquivo em rede ou arquivo local. Os
modos são mutuamente exclusivos. Em `localhost`, o botão **Procurar arquivo**
abre a janela nativa do Windows; em um cliente da LAN, o caminho informado deve
existir no computador servidor. Em ambos os modos a conexão permanece somente
leitura.

> 💡 **Importante**: Mantenha a estrutura completa de pastas. Não mova apenas o arquivo .exe!

### Opção 2: Instalação Python

> Requisito de versão: Python **3.10+**

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

> 📖 **Guia Detalhado**: Veja [INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md) para instruções completas de implantação hospitalar.

## 🌐 Implantação multiestação pela pasta compartilhada

O modo recomendado quando não existe um servidor disponível é manter a pasta
`onedir` completa no compartilhamento e abrir **`Iniciar_Sistema_Rede.bat`** em
cada computador. Não abra o EXE diretamente pela rede: o Windows pode bloquear
o carregamento de `_internal\python311.dll`. O launcher externo copia a versão
para `%LOCALAPPDATA%` antes de iniciar o Python, cria um SQLite
privado por estação e sincroniza alterações criptografadas em até cinco
segundos. **Nunca coloque ou abra um SQLite compartilhado diretamente pela
rede.**

Na primeira estação, guarde a chave de recuperação exibida. Nas demais,
informe essa chave para restaurar o checkpoint e parear o computador. O sistema
continua funcionando offline e publica a outbox quando a rede retorna.

> Leia o procedimento completo em [MULTISTATION_SYNC.md](docs/MULTISTATION_SYNC.md)
> antes de migrar uma instalação com dados existentes.

> O passo a passo de publicação, primeiro acesso, atualização e diagnóstico
> está em [ACESSO_REDE_COPIA_LOCAL.md](docs/ACESSO_REDE_COPIA_LOCAL.md).

Se a política do Windows impedir a execução do BAT diretamente por SMB, copie
`Iniciar_Sistema_Copia_Manual.bat` e `launcher_network.ps1` para a estação,
execute o BAT local e informe o caminho UNC solicitado. O caminho fica salvo no
perfil do usuário e o banco continua fora da pasta da aplicação.

O `run_network.bat` permanece disponível somente para instalações que possuam
um computador servidor continuamente ligado e acesso de firewall. Ele não é
necessário para a implantação offline-first pelo EXE compartilhado.

### 🖥️ Implantação local (uma estação)

Use `run_local.bat` ou abra o executável. Fechar o navegador não encerra o
servidor; use o botão **Encerrar sistema**. O endpoint de encerramento funciona
somente no modo desktop e por conexão direta de `localhost`.

---

## 🔧 Configuração

### Variáveis de Ambiente

Crie arquivo `.env` a partir do `.env.example` e configure:

```bash
# Segurança / sessão
SECRET_KEY=
FLASK_ENV=production
FLASK_DEBUG=0
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=Lax
SESSION_IDLE_TIMEOUT_MINUTES=30

# Configuração do Servidor
SERVER_HOST=0.0.0.0        # 127.0.0.1 para local, 0.0.0.0 para LAN
SERVER_PORT=5000
DESKTOP_MODE=false         # true habilita o botão de encerramento local

# Bootstrap do primeiro administrador
ADMIN_BOOTSTRAP_USERNAME=admin.local
ADMIN_BOOTSTRAP_PASSWORD=123456
ADMIN_BOOTSTRAP_FULL_NAME=Administrador do Sistema
ADMIN_BOOTSTRAP_SPECIALTY=ortopedia

# Integrações opcionais
GOOGLE_CALENDAR_ID=
GOOGLE_CALENDAR_ICS_URL=
GOOGLE_FORMS_PUBLIC_ID=
GOOGLE_FORMS_VIEWFORM_URL=
GOOGLE_FORMS_TIMEOUT=10

# Hardening HTTP
SECURITY_HEADERS_ENABLED=true
SECURITY_CSP_REPORT_ONLY=true
SECURITY_HSTS_ENABLED=false
```

### Opções de Configuração Principais

| Variável | Descrição | Padrão | Obrigatório |
|----------|-----------|--------|-------------|
| `SECRET_KEY` | Chave de criptografia de sessão Flask | gerada em runtime se vazia | Recomendado |
| `SERVER_HOST` | Endereço de binding (127.0.0.1=local, 0.0.0.0=LAN) | 127.0.0.1 | Não |
| `DESKTOP_MODE` | Habilitar o botão local de encerramento manual | false | Não |
| `ADMIN_BOOTSTRAP_USERNAME` | Usuário opcional para bootstrap automatizado | - | Não |
| `ADMIN_BOOTSTRAP_PASSWORD` | PIN opcional de exatamente 6 dígitos para bootstrap automatizado | - | Não |
| `GOOGLE_CALENDAR_ID` | ID opcional do Google Calendar usado para derivar URL ICS padrão | - | Opcional |
| `CALENDAR_CACHE_TTL_SECONDS` | Intervalo de atualização em segundo plano | 300 | Não |
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
# Solução segura: executar o setup idempotente, que cria backup antes de atualizar
setup_windows.bat
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
# - Verificar CALENDAR_CACHE_TTL_SECONDS=300 no .env
# - Atualização manual: POST /agenda/cache/refresh
# - Verificar se URL ICS está acessível
```

**8. Sincronização indisponível ou alterações pendentes**
```text
# O atendimento continua no SQLite local.
# 1. Verifique acesso de leitura/escrita à pasta compartilhada.
# 2. Clique no indicador global para forçar a sincronização.
# 3. Não mova o SQLite local para a rede e não edite _shared_data.
# 4. Consulte docs/MULTISTATION_SYNC.md para pareamento e recuperação.
```
---

## 📊 Status Atual & Roadmap

### ✅ Funcionalidades Prontas para Produção
- Registro e gerenciamento de pacientes
- Fluxo de solicitação de cirurgia com geração de PDF
- Integração Google Calendar com cache de 60 segundos
- Agendamento automatizado via Google Forms
- Rastreamento de status de eventos (realizada/suspensa)
- Implantação multiestação offline-first com envelopes AES-256-GCM
- Perfil autogerenciável e autenticação com PIN

### ⚠️ Limitações Conhecidas
- **Sem autenticação avançada** - Sistema simples de seleção de usuário
- **Consistência eventual** - alterações remotas podem levar até cinco segundos
- **Sem servidor transacional central** - conflitos simultâneos usam última alteração por campo
- **Pareamento obrigatório** - novas estações exigem a chave de recuperação
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
- ✅ **Otimizado para multiestação** - cópia local versionada e funcionamento offline
- ✅ **Servidor de produção** - Waitress WSGI (sem servidor de desenvolvimento)
- ✅ **Eficiente em recursos** - <50MB RAM, uso mínimo de CPU
- ✅ **Persistência de dados** - SQLite local com outbox na mesma transação
- ⚠️ **Backup obrigatório** - Backup manual do banco necessário
- ⚠️ **Consistência eventual** - sem transação distribuída entre computadores

---

## 📖 Documentação Adicional

- **[INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** - Guia completo de implantação hospitalar
- **[QUICK_START.md](docs/QUICK_START.md)** - Guia rápido para começar em 3 passos
- **[TROUBLESHOOTING_ESPECIALIDADES.md](docs/TROUBLESHOOTING_ESPECIALIDADES.md)** - Diagnóstico e soluções
- **[.env.example](.env.example)** - Modelo de configuração com todas as variáveis
- **[Requirements](requirements.txt)** - Dependências Python com versões
- **[Geração de PDFs](docs/PDF_GENERATION.md)** - Inventário, mapeamentos, validação e testes PyMuPDF
- **[Multiestação](docs/MULTISTATION_SYNC.md)** - Pareamento, criptografia, conflitos, recuperação e atualização
- **[Atualização para a v2.7](docs/ATUALIZACAO_V2.7.md)** - Passo a passo para rede, EXE local e instalação Python
- **[Frontend](docs/FRONTEND.md)** - Vite, HTMX, Alpine.js, ícones Lucide e comandos `npm`

---

## 📄 Licença

Licença MIT - Veja [LICENSE](LICENSE) para detalhes.

---

## 👨‍⚕️ Autor

**Dr. Pedro Henrique Freitas**
- Sistema desenvolvido para otimização do fluxo de trabalho em Ortopedia
- © 2026 - Todos os direitos reservados

---

## 📞 Suporte

Para relatar bugs ou solicitar recursos, abra uma [Issue](../../issues).

---

<div align="center">

**Desenvolvido com ❤️ para Ortopedia**

[⬆ Voltar ao topo](#-sistema-de-registro-de-pacientes--gerenciamento-de-cirurgias)

</div>
