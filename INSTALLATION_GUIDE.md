# Guia de Instalação para Implantação Hospitalar

**Sistema de Registro de Pacientes & Gerenciamento de Cirurgias**

*Guia completo de implantação para ambientes hospitalares/clínicas Windows*

---

## Sumário

1. [Pré-requisitos](#1-pré-requisitos)
2. [Download & Atualização](#2-download--atualização)
3. [Configuração do Ambiente](#3-configuração-do-ambiente)  
4. [Configuração](#4-configuração)
5. [Inicialização do Banco de Dados](#5-inicialização-do-banco-de-dados)
6. [Implantação de Rede LAN](#6-implantação-de-rede-lan)
7. [Configuração do Windows Firewall](#7-configuração-do-windows-firewall)
8. [Modo de Serviço de Inicialização Automática](#8-modo-de-serviço-de-inicialização-automática)
9. [Procedimentos de Manutenção](#9-procedimentos-de-manutenção)
10. [Solução de Problemas](#10-solução-de-problemas)
11. [Segurança & Governança](#11-segurança--governança)
12. [Apêndice](#12-apêndice)

---

## 1. Pré-requisitos

### 1.1 Sistemas Operacionais Suportados
- **Windows 10** (versão 1909 ou posterior)
- **Windows 11** (todas as versões)
- **Windows Server 2019/2022** (recomendado para ambientes hospitalares)

### 1.2 Requisitos de Hardware
**Mínimo:**
- CPU: 2 cores, 2,0 GHz
- RAM: 4 GB
- Armazenamento: 2 GB de espaço livre
- Rede: Ethernet 100 Mbps

**Recomendado para LAN Hospitalar:**
- CPU: 4 cores, 2,5 GHz
- RAM: 8 GB
- Armazenamento: 10 GB de espaço livre (para crescimento do banco de dados)
- Rede: Ethernet 1 Gbps
- Endereço IP fixo (recomendado)

### 1.3 Pré-requisitos de Rede
- **Acesso LAN**: Endereço IP estático preferencial
- **Disponibilidade de Porta**: Porta TCP 5000 deve estar disponível
- **Firewall**: Configurar Windows Firewall para conexões de entrada
- **DNS**: Resolução de hostname para o servidor (opcional mas recomendado)

### 1.4 Pré-requisitos de Software
**Python 3.11 ou posterior** (se usando método de instalação Python):
```powershell
# Download de: https://www.python.org/downloads/
# Ou verificar se instalado:
python --version
# Deve mostrar Python 3.11.x ou posterior
```

**Git** (opcional, para atualizações):
```powershell
# Download de: https://git-scm.com/download/win
git --version
```

---

## 2. Download & Atualização

### 2.1 Opção A: Download do Executável (Recomendado)
1. **Baixe** a versão mais recente das releases do GitHub
2. **Extraia** para um local permanente (ex: `C:\\PatientRegistration\\`)
3. **Preserve** a estrutura completa de pastas

### 2.2 Opção B: Git Clone (Para Atualizações)
```powershell
# Clone inicial
cd C:\\
git clone https://github.com/phgutierrez/patient-registration-system.git
cd patient-registration-system

# Atualizações futuras
git pull origin main
```

### 2.3 Procedimento de Atualização (Preservar Configuração Local)
```powershell
# 1. Backup do arquivo .env atual
copy .env .env.backup

# 2. Backup do banco de dados
copy instance\\prontuario.db instance\\prontuario_backup_YYYY-MM-DD.db

# 3. Atualizar código (método Git)
git stash                    # Guardar alterações locais
git pull origin main        # Obter código mais recente
git stash pop               # Restaurar alterações locais

# 4. Restaurar configuração
copy .env.backup .env

# 5. Atualizar dependências (se usando Python)
pip install -r requirements.txt
```

---

## 3. Configuração do Ambiente

### 3.1 Opção A: Ambiente Virtual Python (Padrão)

**Passo 1: Criar Ambiente Virtual**
```powershell
cd C:\\patient-registration-system
python -m venv .venv
```

```powershell
.venv\Scripts\activate.bat
# Você deve ver (.venv) no seu prompt
```

**Passo 3: Instalar Dependências**
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**Passo 4: Verificar Instalação**
```powershell
python -c "import flask; print('Versão Flask:', flask.__version__)"
python -c "import waitress; print('Waitress instalado com sucesso')"
```

### 3.2 Opção B: Python Portável (Avançado)
Se sua organização exigir instalações portáveis:

1. Baixe **WinPython** ou **Portable Python**
2. Extraia para `C:\PatientRegistration\python\`
3. Configure PATH nos scripts batch para usar Python portável

---

## 4. Configuração

### 4.1 Criar Arquivo de Ambiente
```powershell
# Copiar template
copy .env.example .env

# Editar com notepad ou editor de sua preferência
notepad .env
```

### 4.2 Variáveis de Configuração Essenciais

**Configuração Básica:**
```properties
# Segurança Flask (OBRIGATÓRIO - Gerar chave única)
SECRET_KEY=chave-secreta-unica-hospital-mude-isso-2026

# Ambiente Flask
FLASK_ENV=production
FLASK_DEBUG=0

# Configuração do Servidor para LAN
SERVER_HOST=0.0.0.0          # Ouvir em todas as interfaces
SERVER_PORT=5000             # Porta padrão, mude se necessário
DESKTOP_MODE=false           # Desabilitar auto-desligamento para LAN

# Banco de Dados (Opcional - usa localização SQLite padrão)
# SQLALCHEMY_DATABASE_URI=sqlite:///instance/prontuario.db
```

**Integração Google Calendar (OBRIGATÓRIO):**
```properties
# Obter em Configurações do Google Calendar → Integrar Calendário
GOOGLE_CALENDAR_ID=calendario-hospital@group.calendar.google.com
GOOGLE_CALENDAR_TZ=America/Fortaleza                # Ou seu fuso horário
GOOGLE_CALENDAR_ICS_URL=https://calendar.google.com/calendar/ical/SEU_ID_CALENDARIO/public/basic.ics

# Configurações de cache (60 segundos = atualização a cada 1 minuto)
CALENDAR_CACHE_TTL_SECONDS=60
```

**Automação Google Forms (OPCIONAL):**
```properties
# Para agendamento automático de cirurgias
GOOGLE_FORMS_PUBLIC_ID=1FAIpQLSc...seu-id-publico-form
GOOGLE_FORMS_VIEWFORM_URL=https://docs.google.com/forms/d/e/SEU_ID_PUBLICO/viewform
GOOGLE_FORMS_TIMEOUT=10
```

### 4.3 Como Obter Valores de Configuração

**ID do Google Calendar:**
1. Abrir Google Calendar
2. Configurações → Configurações do Calendário → [Seu Calendário]
3. Seção "Integrar Calendário" → ID do Calendário
4. Copiar o ID semelhante a email

**URL ICS:**
1. Mesma página de configurações do calendário
2. Seção "Integrar Calendário" → Calendário público
3. Tornar calendário público → Copiar link ICS

**ID Público do Google Forms:**
1. Abrir seu Google Form
2. Clicar "Enviar" → Copiar link
3. Extrair ID da URL: `/d/e/[ESTE_É_O_ID_PUBLICO]/viewform`
4. **Importante**: Use ID PÚBLICO, não ID de edição!

### 4.4 Configuração Avançada (Opcional)
```properties
# Gerenciamento de Ciclo de Vida (Apenas Modo Desktop)
LIFECYCLE_TIMEOUT_SECONDS=30      # Timeout de auto-desligamento
LIFECYCLE_HEARTBEAT_SECONDS=5     # Intervalo de heartbeat

# Timeout de Conexão do Banco de Dados
# SQLALCHEMY_ENGINE_OPTIONS={"pool_timeout": 20, "pool_recycle": -1}

# Limites de Upload de Arquivo
# MAX_CONTENT_LENGTH=16777216      # Tamanho máximo de arquivo 16MB
```

---

## 5. Inicialização do Banco de Dados

### 5.1 Configuração Automática (Recomendado)
O sistema usa criação direta de tabelas, não são necessárias migrações manuais:

```powershell
# Testar criação do banco de dados
.venv\Scripts\activate.bat
python create_tables_direct.py

# Saída esperada:
# "All tables created successfully!"
# "✓ Columns ETag and Last-Modified were created correctly!"
```

### 5.2 Verificar Esquema do Banco de Dados
```powershell
python -c "
from src.app import create_app
app = create_app()
with app.app_context():
    from src.extensions import db
    inspector = db.inspect(db.engine)
    print('Tabelas:', inspector.get_table_names())
    # Deve mostrar: ['calendar_cache', 'calendar_event_status', 'patient', 'surgery_requests', 'users']
"
```

### 5.3 Localização do Banco de Dados
- **Localização padrão**: `instance/prontuario.db`
- **Caminho completo**: `C:\patient-registration-system\instance\prontuario.db`
- **Localização do backup**: Criar backups na pasta `instance/`

---

## 6. Implantação de Rede LAN

### 6.1 Inicialização Manual do Servidor de Produção
```powershell
# Navegar para o diretório do projeto
cd C:\patient-registration-system

# Ativar ambiente virtual
.venv\Scripts\activate.bat

# Definir ambiente de produção
set SERVER_HOST=0.0.0.0
set SERVER_PORT=5000
set DESKTOP_MODE=false
set FLASK_ENV=production
set FLASK_DEBUG=0

# Iniciar servidor Waitress
waitress-serve --listen=0.0.0.0:5000 wsgi:application
```

### 6.2 Usando Script Batch (Recomendado)
**Verificar se `run_network.bat` existe:**
```batch
@echo off
REM Modo rede - Executar app Flask na LAN usando Waitress
echo Iniciando Sistema de Registro de Pacientes no modo REDE...

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Definir configuração do modo rede
set SERVER_HOST=0.0.0.0
set SERVER_PORT=5000
set DESKTOP_MODE=false
set FLASK_ENV=production
set FLASK_DEBUG=0

REM Iniciar a aplicação com Waitress
echo Iniciando servidor... Pressione Ctrl+C para parar.
echo Acesso deste computador: http://localhost:5000
echo Acesso da rede: http://SEU_ENDERECO_IP:5000
waitress-serve --listen=%SERVER_HOST%:%SERVER_PORT% wsgi:application
```

**Executar:**
```powershell
# Duplo clique em run_network.bat ou executar da linha de comando:
run_network.bat
```

### 6.3 Verificar Implantação de Rede
```powershell
# Verificar se servidor está rodando na porta correta
netstat -an | findstr :5000

# Testar acesso local
curl http://localhost:5000
# Ou abrir no navegador: http://localhost:5000

# Obter endereço IP do servidor
ipconfig | findstr "IPv4"
# Testar de outro PC: http://IP_SERVIDOR:5000
```

---

## 7. Configuração do Windows Firewall

### 7.1 Regra Automática (PowerShell - Executar como Administrador)
```powershell
# Permitir conexões TCP de entrada na porta 5000 para redes privadas
netsh advfirewall firewall add rule name="Patient Registration System" dir=in action=allow protocol=TCP localport=5000 profile=private

# Verificar criação da regra
netsh advfirewall firewall show rule name="Patient Registration System"
```

### 7.2 Configuração Manual (Método GUI)

**Passo 1: Abrir Windows Firewall**
1. Painel de Controle → Sistema e Segurança → Windows Defender Firewall
2. Clicar "Configurações avançadas" (painel esquerdo)

**Passo 2: Criar Regra de Entrada**
1. Clicar com botão direito "Regras de Entrada" → "Nova Regra"
2. Tipo de Regra: **Porta** → Próximo
3. Protocolo e Portas:
   - **TCP**
   - Portas Locais Específicas: **5000**
   - Próximo

**Passo 3: Configurar Ação**
1. Ação: **Permitir a conexão** → Próximo
2. Perfil: Marcar **Privado** (desmarcar Domínio e Público por segurança) → Próximo
3. Nome: **Patient Registration System** → Finalizar

### 7.3 Testar Configuração do Firewall
```powershell
# De outro computador na rede:
# 1. Testar conectividade básica (ping)
ping ENDERECO_IP_SERVIDOR

# 2. Testar conectividade da porta (telnet)
telnet ENDERECO_IP_SERVIDOR 5000
# Deve conectar sem erros

# 3. Testar acesso web (navegador)
# Abrir: http://ENDERECO_IP_SERVIDOR:5000
```

---

## 8. Auto-Start Service Mode

### 8.1 Option A: Windows Task Scheduler (Recommended)

**Step 1: Create Task**
1. Open **Task Scheduler** (taskschd.msc)
2. Action → Create Basic Task
3. Name: **Patient Registration System**
4. Trigger: **When the computer starts**
5. Action: **Start a program**

**Passo 2: Configurar Programa**
- **Programa/Script**: `C:\\patient-registration-system\\run_network.bat`
- **Iniciar em**: `C:\\patient-registration-system`
- **Executar independente de usuário logado**: ✓
- **Executar com privilégios mais altos**: ✓

**Passo 3: Definir Conta de Usuário**
1. Clicar com botão direito na tarefa → Propriedades
2. Aba Geral → Alterar Usuário ou Grupo
3. Inserir: **SYSTEM** ou usar conta de serviço dedicada
4. Senha: Não obrigatória para conta SYSTEM

### 8.2 Option B: NSSM (Non-Sucking Service Manager)

**Step 1: Download NSSM**
1. Download from: https://nssm.cc/download
2. Extract `nssm.exe` to `C:\\Windows\\System32\\`

**Step 2: Install Service**
```powershell
# Run as Administrator
nssm install "PatientRegistrationSystem"

# Configuration will open - fill in:
# Path: C:\\patient-registration-system\\.venv\\Scripts\\python.exe
# Startup Directory: C:\\patient-registration-system
# Arguments: -m waitress --listen=0.0.0.0:5000 wsgi:application

# Set environment variables in "Environment" tab:
# FLASK_ENV=production
# DESKTOP_MODE=false
# SERVER_HOST=0.0.0.0
```

**Passo 3: Iniciar Serviço**
```powershell
nssm start "PatientRegistrationSystem"

# Verificar status
nssm status "PatientRegistrationSystem" 

# Parar serviço
nssm stop "PatientRegistrationSystem"

# Remover serviço (se necessário)
nssm remove "PatientRegistrationSystem"
```

### 8.3 Verificar Inicialização Automática
```powershell
# Reiniciar servidor e verificar se serviço inicia automaticamente
# Verificar com:
netstat -an | findstr :5000
# Deve mostrar LISTENING em 0.0.0.0:5000

# Testar acesso web
curl http://localhost:5000
```

---

## 9. Maintenance Procedures

### 9.1 Regular Updates

**Monthly Update Process:**
```powershell
# 1. Stop the service
nssm stop "PatientRegistrationSystem"
# Or stop Task Scheduler task

# 2. Backup database
copy instance\\prontuario.db "instance\\backup_%DATE:~-4,4%-%DATE:~-10,2%-%DATE:~-7,2%.db"

# 3. Backup configuration
copy .env .env.backup

# 4. Update code (Git method)
git pull origin main

# 5. Update dependencies
.venv\\Scripts\\activate.bat
pip install --upgrade -r requirements.txt

# 6. Test configuration
python -c "from src.app import create_app; app=create_app(); print('Config OK')"

# 7. Restart service
nssm start "PatientRegistrationSystem"

# 8. Verify
curl http://localhost:5000
```

### 9.2 Manutenção do Banco de Dados

**Backup Semanal:**
```batch
@echo off
set backup_date=%DATE:~-4,4%-%DATE:~-10,2%-%DATE:~-7,2%
copy "C:\patient-registration-system\instance\prontuario.db" "C:\Backups\PatientDB\prontuario_%backup_date%.db"
echo Backup do banco de dados concluído: %backup_date%
```

**Otimização do Banco de Dados (Mensal):**
```powershell
# SQLite VACUUM (recuperar espaço e otimizar)
python -c "
import sqlite3
conn = sqlite3.connect('instance/prontuario.db')
conn.execute('VACUUM')
conn.close()
print('Banco de dados otimizado')
"
```

### 9.3 Gerenciamento de Logs

**Visualizar Logs da Aplicação:**
```powershell
# Se logging estiver configurado, verificar:
type logs\\app.log | findstr ERROR
type logs\\app.log | findstr WARNING

# Visualizador de Eventos do Windows para logs de serviço:
eventvwr.msc
```

**Limpar Logs Antigos:**
```powershell
# Rotacionar logs (se implementado)
# Ou excluir arquivos manualmente
forfiles /p C:\\patient-registration-system\\logs /s /m *.log /d -30 /c "cmd /c del @path"
```

---

## 10. Troubleshooting

### 10.1 Server Won't Start

**Problem: "Port already in use"**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID with actual process ID)
taskkill /PID 1234 /F

# Restart server
run_network.bat
```

**Problem: "Module not found" errors**
```powershell
# Verify virtual environment
.venv\\Scripts\\activate.bat
pip list | findstr flask
pip list | findstr waitress

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### 10.2 Problemas de Acesso à Rede

**Problema: Não consegue acessar de outros computadores**
```powershell
# Verificar se servidor está ouvindo em todas as interfaces
netstat -an | findstr :5000
# Deve mostrar: 0.0.0.0:5000, não 127.0.0.1:5000

# Verificar regra do Windows Firewall
netsh advfirewall firewall show rule name="Patient Registration System"

# Testar com Windows Firewall temporariamente desabilitado
netsh advfirewall set allprofiles state off
# !! Lembrar de reabilitar: netsh advfirewall set allprofiles state on

# Obter endereço IP correto
ipconfig | findstr "IPv4"
# Testar do cliente: ping ENDERECO_IP
```

**Problema: Performance de rede lenta**
```powershell
# Verificar velocidade da interface de rede
wmic path Win32_PerfRawData_Tcpip_NetworkInterface get Name,BytesTotalPerSec

# Monitorar uso de rede em tempo real
perfmon.exe
# Adicionar: Network Interface → Bytes Total/sec
```

### 10.3 Problemas do Banco de Dados

**Problema: "Database is locked"**
```powershell
# 1. Parar todas as instâncias do servidor
nssm stop "PatientRegistrationSystem"

# 2. Verificar arquivos de bloqueio obsoletos
del instance\.*.db-journal
del instance\*.db-wal

# 3. Reiniciar servidor
nssm start "PatientRegistrationSystem"
```

**Problema: Erros "No such table"**
```powershell
# Recriar esquema do banco de dados
python create_tables_direct.py

# Verificar se tabelas existem
python -c "
import sqlite3; 
conn = sqlite3.connect('instance/prontuario.db'); 
cursor = conn.cursor(); 
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"); 
print('Tabelas:', cursor.fetchall())
"
```

### 10.4 Problemas de Integração de Calendário

**Problema: Calendário não atualiza**
```powershell
# Verificar acessibilidade da URL ICS
curl "SUA_URL_ICS_DO_CALENDARIO"
# Deve retornar dados do calendário

# Testar endpoint de atualização de cache
curl -X POST http://localhost:5000/agenda/cache/refresh

# Verificar configurações de cache no .env
type .env | findstr CALENDAR
```

**Problema: Fuso horário/datas incorretos**
```powershell
# Verificar configuração de fuso horário
python -c "
import pytz
print('Disponível:', 'America/Fortaleza' in pytz.all_timezones)
print('TZ Atual:', pytz.timezone('America/Fortaleza'))
"

# Atualizar fuso horário no .env
echo GOOGLE_CALENDAR_TZ=America/Fortaleza >> .env
```

### 10.5 Problemas de Integração Google Forms

**Problema: Erros 404 no envio de formulário**
```powershell
# Verificar formato da URL do formulário (ID PÚBLICO, não ID DE EDIÇÃO)
# Correto: https://docs.google.com/forms/d/e/ID_PUBLICO/viewform
# Errado:  https://docs.google.com/forms/d/ID_EDICAO/edit

# Testar acessibilidade do formulário
curl "https://docs.google.com/forms/d/e/SEU_ID_PUBLICO/viewform"
# Deve retornar HTML do formulário
```

### 10.6 Problemas de Inicialização Automática do Serviço

**Problema: Serviço não inicia no boot**
```powershell
# Verificar tarefa do Agendador de Tarefas
schtasks /query /tn "Patient Registration System"

# Verificar serviço NSSM
nssm status "PatientRegistrationSystem"
sc query "PatientRegistrationSystem"

# Verificar Log de Eventos do Windows para erros
eventvwr.msc → Logs do Windows → Sistema
# Procurar por falhas na inicialização do serviço
```

---

## 11. Segurança & Governança

### 11.1 Segurança de Rede

**Configuração Recomendada:**
- **Apenas LAN**: Nunca expor à internet sem auditoria de segurança adequada
- **Firewall**: Permitir apenas acesso de rede privada (não público/domínio)
- **Restrições de IP**: Considerar limitar a sub-redes específicas se necessário
- **SSL/HTTPS**: Não implementado - considerar proxy reverso (nginx/IIS) para HTTPS

**Isolamento de Rede:**
```powershell
# Restringir a sub-rede específica (regra de firewall avançada)
netsh advfirewall firewall add rule name="PatientReg-Subnet" dir=in action=allow protocol=TCP localport=5000 remoteip=192.168.1.0/24
```

### 11.2 Proteção de Dados

**Segurança do Banco de Dados:**
- **Permissões de Arquivo**: Restringir acesso a `instance/prontuario.db` à conta de serviço
- **Backups**: Criptografar arquivos de backup se armazenados em compartilhamentos de rede
- **Cuidado com PHI**: Dados médicos no banco - garantir conformidade com leis locais de privacidade

**Controle de Acesso:**
- **Autenticação Básica**: Sistema usa seleção simples de usuário (não seguro para dados sensíveis)
- **Recomendação**: Implementar autenticação adequada para uso em produção
- **Trilha de Auditoria**: Limitada - considerar implementar logging abrangente

### 11.3 Backup Strategy

**Daily Automated Backup:**
```batch
@echo off
REM Daily backup script
set backup_dir=\\NetworkShare\\PatientRegistrationBackups
set date_stamp=%DATE:~-4,4%-%DATE:~-10,2%-%DATE:~-7,2%

REM Create backup directory
mkdir "%backup_dir%\\%date_stamp%" 2>NUL

REM Backup database
copy "C:\\patient-registration-system\\instance\\prontuario.db" "%backup_dir%\\%date_stamp%\\database.db"

REM Backup configuration
copy "C:\\patient-registration-system\\.env" "%backup_dir%\\%date_stamp%\\config.env"

REM Backup generated PDFs (optional)
xcopy "C:\\patient-registration-system\\src\\static\\pdfs\\gerados\\*" "%backup_dir%\\%date_stamp%\\pdfs\\" /E /I /Y

echo Backup completed: %date_stamp%
```

**Retention Policy:**
```batch
REM Delete backups older than 30 days
forfiles /p "\\NetworkShare\\PatientRegistrationBackups" /d -30 /c "cmd /c rmdir /s /q @path"
```

### 11.4 Considerações de Conformidade

**HIPAA/Privacidade (se aplicável):**
- Sistema armazena PHI (Informações de Saúde Protegidas)
- Implementar controles de acesso adequados e logging de auditoria
- Avaliações de segurança regulares recomendadas
- Considerar criptografia de dados em repouso

**Governança de TI Hospitalar:**
- Documentar todas as alterações de configuração
- Manter processo de gerenciamento de mudanças
- Avaliações regulares de vulnerabilidade
- Treinamento da equipe sobre acesso ao sistema e manuseio de dados

---

## 12. Apêndice

### 12.1 Exemplo Completo de .env

```properties
# =================================================================
# Sistema de Registro de Pacientes - Template de Configuração Hospitalar
# =================================================================

# Segurança Flask (OBRIGATÓRIO - Gerar chave única para seu hospital)
SECRET_KEY=chave-secreta-unica-hospital-mude-isso-2026-string-aleatoria-muito-longa

# Ambiente Flask
FLASK_ENV=production
FLASK_DEBUG=0

# Configuração do Servidor
SERVER_HOST=0.0.0.0                    # 0.0.0.0 para acesso LAN, 127.0.0.1 apenas local
SERVER_PORT=5000                       # Mudar se houver conflitos de porta
DESKTOP_MODE=false                     # false para LAN/multi-usuário, true para auto-desligamento desktop

# Configuração do Banco de Dados (Opcional - padrão SQLite)
# SQLALCHEMY_DATABASE_URI=sqlite:///instance/prontuario.db
# SQLALCHEMY_ENGINE_OPTIONS={"pool_timeout": 20, "pool_recycle": -1}

# Integração Google Calendar (OBRIGATÓRIO)
GOOGLE_CALENDAR_ID=s4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com
GOOGLE_CALENDAR_TZ=America/Fortaleza   # Ou America/Sao_Paulo, America/New_York, etc.
GOOGLE_CALENDAR_ICS_URL=https://calendar.google.com/calendar/ical/SEU_ID_CALENDARIO/public/basic.ics

# Cache de Calendário (Performance)
CALENDAR_CACHE_TTL_SECONDS=60          # 60 = atualização a cada 1 minuto
CALENDAR_CACHE_TTL_MINUTES=5           # Configuração legada (usar SECONDS ao invés)

# Integração Google Forms (OPCIONAL - para agendamento automático)
GOOGLE_FORMS_PUBLIC_ID=1FAIpQLScXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GOOGLE_FORMS_VIEWFORM_URL=https://docs.google.com/forms/d/e/ID_PUBLICO/viewform
GOOGLE_FORMS_TIMEOUT=10                # Timeout em segundos para envio do formulário

# Gerenciamento de Ciclo de Vida (Apenas Modo Desktop)
LIFECYCLE_TIMEOUT_SECONDS=30           # Timeout de auto-desligamento (modo desktop)
LIFECYCLE_HEARTBEAT_SECONDS=5          # Intervalo de verificação de heartbeat (modo desktop)

# Limites de Upload de Arquivo (Opcional)
# MAX_CONTENT_LENGTH=16777216          # Tamanho máximo de arquivo 16MB

# Configuração de Logging (Opcional)
# LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR
# LOG_FILE=logs/app.log                # Localização do arquivo de log

# Desenvolvimento/Teste (Não usar em produção)
# AUTO_MIGRATE=false                   # Migração automática do banco de dados
# DEBUG_SQL=false                      # Logar todas as consultas SQL
```

### 12.2 Useful Commands Reference

**Server Management:**
```powershell
# Start server manually
.venv\\Scripts\\activate.bat && waitress-serve --listen=0.0.0.0:5000 wsgi:application

# Start with batch script
run_network.bat

# Check server status
netstat -an | findstr :5000
curl http://localhost:5000/api/heartbeat

# Stop server (Ctrl+C in terminal, or kill process)
taskkill /IM python.exe /F
```

**Database Operations:**
```powershell
# Create/recreate database
python create_tables_direct.py

# Backup database
copy instance\\prontuario.db instance\\backup_%DATE%.db

# Database information
python -c "import sqlite3; conn=sqlite3.connect('instance/prontuario.db'); print('Tables:', [row[0] for row in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')])"

# Optimize database
python -c "import sqlite3; conn=sqlite3.connect('instance/prontuario.db'); conn.execute('VACUUM'); conn.close(); print('Database optimized')"
```

**Network Diagnostics:**
```powershell
# Get server IP
ipconfig | findstr IPv4

# Test network connectivity
ping SERVER_IP
telnet SERVER_IP 5000

# Check firewall rules
netsh advfirewall firewall show rule name="Patient Registration System"

# Monitor network usage
netstat -e
```

**Service Management:**
```powershell
# NSSM commands
nssm status "PatientRegistrationSystem"
nssm start "PatientRegistrationSystem"
nssm stop "PatientRegistrationSystem"
nssm restart "PatientRegistrationSystem"

# Task Scheduler
schtasks /query /tn "Patient Registration System"
schtasks /run /tn "Patient Registration System"
```

### 12.3 Alternativas de Configuração de Porta

Se a porta 5000 não estiver disponível, modifique estes arquivos:

**Arquivo .env:**
```properties
SERVER_PORT=8080                       # Mudar para porta disponível
```

**Regra de firewall:**
```powershell
netsh advfirewall firewall add rule name="Patient Registration System" dir=in action=allow protocol=TCP localport=8080 profile=private
```

**Scripts batch (run_network.bat):**
```batch
set SERVER_PORT=8080
waitress-serve --listen=%SERVER_HOST%:%SERVER_PORT% wsgi:application
```

### 12.4 Configurações Comuns de Rede Hospitalar

**Configuração de IP Estático:**
```powershell
# Definir IP estático (substituir pelos valores da sua rede)
netsh interface ip set address "Conexão Local" static 192.168.1.100 255.255.255.0 192.168.1.1
netsh interface ip set dns "Conexão Local" static 8.8.8.8
```

**Registro DNS (ambientes Windows Server):**
```powershell
# Registrar hostname no DNS
nslookup PatientRegistration-Server
# Deve resolver para o endereço IP do servidor
```

**Considerações de Domínio:**
- **Ingressado no Domínio**: Serviço pode executar com conta de serviço do domínio
- **Grupo de Trabalho**: Usar conta de serviço local (SYSTEM ou conta dedicada)
- **Autenticação**: Considerar integração LDAP para ambientes de domínio

---

## Suporte & Contato

Para suporte técnico ou assistência na implantação:

- **Issues do GitHub**: [Relatar bugs ou solicitar recursos](https://github.com/phgutierrez/patient-registration-system/issues)
- **Documentação**: Documentação completa do sistema em README.md
- **Emergência**: Manter procedimentos de restauração de backup documentados

---

**Lista de Verificação de Implantação:**
- [ ] Servidor atende requisitos de hardware
- [ ] Python 3.11+ instalado e funcionando
- [ ] Banco de dados criado e acessível
- [ ] Arquivo .env configurado com todas as variáveis obrigatórias
- [ ] Regra do Windows Firewall criada e testada
- [ ] Acesso de rede verificado de computadores cliente
- [ ] Serviço de inicialização automática configurado e testado
- [ ] Procedimentos de backup implementados e testados
- [ ] Equipe treinada no acesso ao sistema e solução básica de problemas

**© 2026 - Guia de Implantação Hospitalar - Dr. Pedro Henrique Freitas**