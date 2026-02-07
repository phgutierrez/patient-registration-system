# 🏥 Sistema de Solicitação de Cirurgia - Ortopedia Pediátrica

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11.9-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3.3-black?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Produção-success)

Sistema completo para gerenciamento de pacientes e solicitações de cirurgia pediátrica com interface moderna e geração automática de documentos.

[📥 Download](#-instalação) • [📖 Documentação](#-funcionalidades) • [🚀 Como Usar](#-uso-rápido) • [📄 Releases](../../releases)

</div>

---

## 📋 Sobre o Projeto

Sistema desenvolvido para otimizar o processo de cadastro de pacientes e solicitação de cirurgias ortopédicas pediátricas. Inclui geração automática de PDFs, integração com banco de dados local e interface responsiva moderna.

### ✨ Características Principais

- 🎨 **Interface Moderna** - Design responsivo com gradientes e animações
- ⚡ **Alta Performance** - Servidor Waitress otimizado para produção
- 💾 **Persistência Local** - SQLite com migrações automáticas (Alembic)
- 📄 **Geração de PDFs** - Documentos automáticos com ReportLab
- 🔒 **Segurança** - Autenticação de usuários e proteção CSRF
- 🚀 **Executável Windows** - Sem necessidade de instalação Python

---

## 🎯 Funcionalidades

### Gestão de Pacientes
- ✅ Cadastro completo com dados pessoais, endereço e informações médicas
- ✅ Listagem com busca e filtros
- ✅ Edição e visualização de prontuários
- ✅ Integração com banco Access (CPAM) via pyodbc
- ✅ Validação automática de dados (CNS, CID, telefone)
- ✅ Cálculo automático de idade

### Solicitações de Cirurgia
- ✅ Formulário completo para solicitação
- ✅ Geração automática de PDF com dados do paciente
- ✅ Histórico de solicitações por paciente
- ✅ Confirmação e download de documentos
- ✅ **Agendamento Automático via Google Forms**
  - Preview antes de enviar
  - Submissão direta ao Forms
  - Evento criado automaticamente no Google Calendar
  - Proteção contra duplicação

### Gestão de Usuários
- ✅ Cadastro de médicos solicitantes
- ✅ Campos para CNS e CRM
- ✅ Sistema de seleção de usuário ativo
- ✅ Interface de gerenciamento

### Interface do Sistema
- ✅ Dashboard com atalhos rápidos (Alt+N, Alt+L, Alt+U)
- ✅ Cards clicáveis para navegação intuitiva
- ✅ Logo institucional e identidade visual
- ✅ Botão de encerramento do sistema
- ✅ Mensagens de feedback em tempo real

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.11.9** - Linguagem principal
- **Flask 2.3.3** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **Alembic** - Migrações de banco de dados
- **Waitress 2.1.2** - Servidor WSGI de produção
- **Flask-Login** - Gerenciamento de sessões
- **Flask-WTF** - Formulários com validação

### Frontend
- **Bootstrap 5.3.3** - Framework CSS
- **Font Awesome 6.4.0** - Ícones
- **JavaScript** - Interatividade e validações

### Geração de Documentos
- **ReportLab** - Criação de PDFs
- **PyPDF2** - Manipulação de PDFs

### Banco de Dados
- **SQLite** - Banco principal
- **pyodbc** - Integração com Access (CPAM)

---

## 📦 Instalação

### Opção 1: Executável Windows (Recomendado)

1. **Baixe a última versão** na aba [Releases](../../releases)
2. **Extraia a pasta** `PatientRegistration` para um local de sua preferência
3. **Execute** `PatientRegistration.exe`
4. O sistema abrirá automaticamente no navegador padrão

> 💡 **Dica**: A pasta completa (377 MB) contém todas as dependências. Não mova apenas o .exe!

### Opção 2: Executar via Python

```bash
# 1. Clone o repositório
git clone https://github.com/phgutierrez/patient-registration-system.git
cd patient-registration-system

# 2. Crie um ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute o sistema
python run.py
```

---

## 🚀 Uso Rápido

### Primeira Execução

1. O sistema criará automaticamente **5 usuários iniciais**:
   - pedro
   - andre
   - brauner
   - savio
   - laecio

2. **Selecione um usuário** para começar

3. Use o **Dashboard** para navegar:
   - **Alt+N** - Cadastrar novo paciente
   - **Alt+L** - Listar pacientes
   - **Alt+U** - Cadastrar usuário

### Fluxo de Trabalho

```
1. Cadastrar Paciente → 2. Ver Pacientes → 3. Solicitar Cirurgia → 4. Download PDF
```

---

## 📁 Estrutura do Projeto

```
patient-registration-system/
├── src/
│   ├── models/          # Modelos do banco de dados
│   │   ├── patient.py
│   │   ├── surgery_request.py
│   │   └── user.py
│   ├── routes/          # Rotas da aplicação
│   │   ├── auth.py
│   │   ├── patients.py
│   │   ├── surgery.py
│   │   └── main.py
│   ├── templates/       # Templates HTML (17 arquivos)
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── auth/
│   │   ├── patient/
│   │   └── surgery/
│   ├── static/          # Arquivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── logo ortoped.png
│   ├── utils/           # Utilitários
│   │   └── pdf_utils.py
│   ├── app.py           # Configuração do Flask
│   ├── config.py        # Configurações
│   └── extensions.py    # Extensões Flask
├── migrations/          # Migrações do banco
├── dist/               # Executável compilado
│   └── PatientRegistration/
│       ├── PatientRegistration.exe
│       └── instance/   # Banco de dados
├── server.py           # Servidor principal
├── build_exe.py        # Script de build
├── requirements.txt    # Dependências Python
└── README.md

```

---

## 🔧 Desenvolvimento

### Requisitos
- Python 3.11+
- pip
- virtualenv

### Executar em modo desenvolvimento

```bash
# Ativar ambiente virtual
.venv\Scripts\activate

# Executar com auto-reload
flask run --reload

# Ou via Python
python run.py
```

### Criar executável

```bash
# Instalar PyInstaller
pip install pyinstaller==6.3.0

# Executar build
python build_exe.py
```

O executável será criado em `dist/PatientRegistration/`

### Migrações de Banco

```bash
# Criar nova migração
flask db migrate -m "descrição"

# Aplicar migrações
flask db upgrade

# Reverter migração
flask db downgrade
```

---

## 🎨 Capturas de Tela

### Dashboard
Interface principal com cards clicáveis e atalhos de teclado

### Cadastro de Paciente
Formulário completo com validação em tempo real

### Lista de Pacientes
Tabela moderna com busca e ações agrupadas

---

## � Integração com Google Calendar

O sistema inclui agendamento automático via **submissão ao Google Forms**, que dispara um Apps Script para criar eventos no Google Calendar.

### ⚙️ Como Configurar

1. **Configure o .env:**
   ```env
   GOOGLE_FORMS_EDIT_ID=1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw
   GOOGLE_FORMS_TIMEOUT=10
   ```

2. **Extraia os entry IDs do Forms:**
   ```bash
   python scripts/extract_forms_entries.py
   ```

3. **Valide a integração:**
   ```bash
   python scripts/validate_forms_integration.py --skip-submit
   ```

4. **Teste com dados reais:**
   - Crie uma solicitação de cirurgia
   - Clique em "Adicionar à Agenda"
   - Confirme no modal de preview
   - Verifique o evento no Google Calendar

### 📚 Documentação Completa

- [Guia Rápido](docs/GUIA_FORMS.md)
- [Documentação Técnica](docs/REVERSAO_FORMS.md)
- [Resumo Executivo](docs/REVERSAO_RESUMO.md)

### 🔄 Fluxo de Agendamento

```
1. Usuário clica "Adicionar à Agenda"
   ↓
2. Sistema mostra preview (título, data, descrição)
   ↓
3. Usuário confirma
   ↓
4. Sistema submete ao Google Forms
   ↓
5. Apps Script da planilha cria evento DIA INTEIRO no Calendar
```

---

## �📝 Changelog
### v2.0.0 (2026-02-05) - Agendamento via Google Forms
- ✨ **NOVA FEATURE:** Agendamento automático via Google Forms
- ✨ Preview + confirmação antes de enviar
- ✨ Submissão direta ao Forms (sem Web App)
- ✨ Proteção contra agendamento duplicado
- 🔄 Reversão: Apps Script Web App → Google Forms
- 📚 Documentação completa da integração
- 🧪 Scripts de validação e testes
- ⚡ Cache automático de entry IDs
### v1.0.0 (2026-01-26)
- ✨ Interface moderna com gradientes e animações
- ✨ Logo institucional na sidebar
- ✨ Cards do dashboard totalmente clicáveis
- ✨ Modo --onedir para inicialização rápida
- 🐛 Correção de logo duplicado
- ⚡ Otimização de performance
- 📦 Build otimizado (377 MB com todas dependências)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍⚕️ Autor

**Dr. Pedro Henrique Freitas**

- Sistema desenvolvido para otimização de processos em Ortopedia Pediátrica
- © 2026 - Todos os direitos reservados

---

## 📞 Suporte

Para reportar bugs ou solicitar features, abra uma [Issue](../../issues).

---

<div align="center">

**Desenvolvido com ❤️ para Ortopedia Pediátrica**

[⬆ Voltar ao topo](#-sistema-de-solicitação-de-cirurgia---ortopedia-pediátrica)

</div>