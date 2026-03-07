#!/bin/bash
# ===============================================================================
# SETUP LINUX - Patient Registration System
# Inicializacao completa do sistema para Linux
# ===============================================================================

# Navegar para a raiz do projeto (independente de onde o script for executado)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

set -e

DEFAULT_SECRET_KEY="patient-reg-secret-key-2026-change-in-production"

generate_secret_key() {
    if command -v openssl > /dev/null 2>&1; then
        openssl rand -hex 32
    else
        python3 - << 'PYEOF'
import secrets
print(secrets.token_hex(32))
PYEOF
    fi
}

echo ""
echo "==============================================================================="
echo " SETUP DO SISTEMA - Patient Registration System"
echo "==============================================================================="
echo ""
echo "Este script realizara tudo que eh necessario para rodar o sistema:"
echo "  1. Verificar Python 3.9+"
echo "  2. Criar ambiente virtual"
echo "  3. Instalar dependencias"
echo "  4. Validar pre-requisitos Linux (PostgreSQL/ODBC)"
echo "  5. Aplicar migracoes + inserir dados iniciais"
echo ""
echo "==============================================================================="
echo ""

# ===================================================================
# VERIFICACAO INICIAL - Diretorio
# ===================================================================
echo "[VERIFICACAO] Verificando diretorio do projeto..."
if [ ! -f "requirements.txt" ]; then
    echo ""
    echo "[ERRO] Arquivo requirements.txt nao encontrado!"
    echo "       Certifique-se de estar no diretorio raiz do projeto."
    echo ""
    exit 1
fi
echo "  [OK] Arquivo requirements.txt encontrado."
echo ""

# ===================================================================
# VERIFICACAO CRITICA - Python 3.9+
# ===================================================================
echo "[VERIFICACAO] Verificando Python 3.9+..."
echo ""

if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 nao foi encontrado no PATH!"
    echo ""
    echo "Solucoes (escolha conforme sua distro):"
    echo "  Ubuntu/Debian:  sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora/RHEL:    sudo dnf install python3 python3-pip"
    echo "  Arch:           sudo pacman -S python python-pip"
    echo ""
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

echo "  Python encontrado: $PYTHON_VERSION"

if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 9 ]; then
    echo "  [OK] Python $MAJOR.$MINOR atende aos requisitos (3.9+ necessario)"
else
    echo ""
    echo "[ERRO] Python $MAJOR.$MINOR eh uma versao incompativel!"
    echo "       Este sistema requer Python 3.9 ou posterior."
    echo ""
    echo "Solucoes:"
    echo "  Ubuntu/Debian:  sudo apt install python3.11 python3.11-venv"
    echo "  Ou: https://www.python.org/downloads/"
    echo ""
    exit 1
fi

echo ""

# Verificar python3-venv disponivel
if ! python3 -m venv --help &> /dev/null; then
    echo "[ERRO] Modulo venv nao encontrado."
    echo "  Ubuntu/Debian: sudo apt install python3-venv python3.${MINOR}-venv"
    echo "  Instale o pacote acima e execute este script novamente."
    exit 1
fi

# ===================================================================
# PRE-SETUP: Criar .env se nao existir
# ===================================================================
if [ ! -f ".env" ]; then
    echo "[PRE-SETUP] Criando arquivo .env com configuracoes padrao..."
    GENERATED_SECRET_KEY="$(generate_secret_key)"
    cat > .env << 'ENVEOF'
# =================================================================
# Patient Registration System - Configuracao do Ambiente
# Gerado automaticamente pelo setup_linux.sh
# =================================================================

SECRET_KEY=__GENERATED_SECRET_KEY__
FLASK_ENV=production
FLASK_DEBUG=0
SERVER_HOST=127.0.0.1
SERVER_PORT=5000
DESKTOP_MODE=false
DATABASE_URL=postgresql+psycopg2://postgres:troque-esta-senha@localhost:5432/patient_registration
GOOGLE_CALENDAR_ID=s4obpr7j3q70p7b4q5o8vsla9k@group.calendar.google.com
GOOGLE_CALENDAR_TZ=America/Fortaleza
CALENDAR_CACHE_TTL_SECONDS=60
CALENDAR_CACHE_TTL_MINUTES=5
GOOGLE_FORMS_EDIT_ID=1krid3-WpncOkRtw0oBh_2oNgdiqr5KKE6ECyxl9t_aw
GOOGLE_FORMS_PUBLIC_ID=1FAIpQLScWpY4kN_mCgK66SWxfAmw6ltQiSZaIjRlLP0NGV7Rsu9DYIg
GOOGLE_FORMS_TIMEOUT=10
APPS_SCRIPT_SCHEDULER_URL=
LIFECYCLE_TIMEOUT_SECONDS=30
LIFECYCLE_HEARTBEAT_SECONDS=5
ENVEOF
    sed -i.bak "s|__GENERATED_SECRET_KEY__|${GENERATED_SECRET_KEY}|" .env && rm -f .env.bak
    echo "  [OK] Arquivo .env criado com sucesso"
else
    echo "[PRE-SETUP] Arquivo .env ja existe (configuracoes preservadas)."
fi
echo ""

# ===================================================================
# PRE-SETUP: Validar configuracao obrigatoria para producao Linux
# ===================================================================
echo "[PRE-SETUP] Validando configuracoes obrigatorias do .env..."

SECRET_KEY_VALUE="$(grep -E '^SECRET_KEY=' .env | tail -n 1 | cut -d '=' -f2-)"
DATABASE_URL_VALUE="$(grep -E '^DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2-)"

if [ -z "$SECRET_KEY_VALUE" ]; then
    echo "[ERRO] SECRET_KEY nao definido no .env"
    exit 1
fi

if [ "$SECRET_KEY_VALUE" = "$DEFAULT_SECRET_KEY" ]; then
    echo "[ERRO] SECRET_KEY padrao detectado. Defina uma chave unica no .env antes de continuar."
    exit 1
fi

if [ -z "$DATABASE_URL_VALUE" ]; then
    echo "[ERRO] DATABASE_URL nao definido no .env"
    echo "       Exemplo: postgresql+psycopg2://usuario:senha@host:5432/database"
    exit 1
fi

if [[ "$DATABASE_URL_VALUE" != postgresql* ]]; then
    echo "[ERRO] DATABASE_URL invalido para producao Linux. Use PostgreSQL."
    echo "       Valor atual: $DATABASE_URL_VALUE"
    exit 1
fi

echo "  [OK] .env validado para producao Linux"
echo ""

# ===================================================================
# PASSO 1: Criar/Verificar Ambiente Virtual
# ===================================================================
echo "[PASSO 1/5] Verificando ambiente virtual..."

if [ ! -d ".venv" ]; then
    echo "  - Criando novo ambiente virtual..."
    python3 -m venv .venv
    echo "  [OK] Ambiente virtual criado"
else
    echo "  [OK] Ambiente virtual ja existe"
fi

echo ""

# ===================================================================
# PASSO 2: Ativar Ambiente Virtual
# ===================================================================
echo "[PASSO 2/5] Ativando ambiente virtual..."

# shellcheck disable=SC1091
source .venv/bin/activate

echo "  [OK] Ambiente virtual ativado"
echo ""

# ===================================================================
# PASSO 3: Instalar Dependencias
# ===================================================================
echo "[PASSO 3/5] Instalando dependencias..."

echo "  - Atualizando pip..."
python3 -m pip install --upgrade pip --quiet

echo "  - Instalando dependencias do requirements.txt..."
pip install -r requirements.txt

echo "  [OK] Dependencias instaladas com sucesso"
echo ""

# ===================================================================
# PASSO 4: Validar pre-requisitos Linux (PostgreSQL/ODBC)
# ===================================================================
echo "[PASSO 4/5] Validando pre-requisitos Linux..."

if ! command -v psql > /dev/null 2>&1; then
    echo "[ERRO] Comando 'psql' nao encontrado. Instale cliente PostgreSQL antes de continuar."
    echo "  Ubuntu/Debian: sudo apt install postgresql-client"
    echo "  RHEL/Fedora:   sudo dnf install postgresql"
    exit 1
fi

if ! command -v odbcinst > /dev/null 2>&1; then
    echo "[ERRO] Comando 'odbcinst' nao encontrado. pyodbc e obrigatorio neste ambiente."
    echo "  Ubuntu/Debian: sudo apt install unixodbc unixodbc-dev"
    echo "  RHEL/Fedora:   sudo dnf install unixODBC unixODBC-devel"
    exit 1
fi

if ! python3 - << 'PYEOF'
import pyodbc
print(pyodbc.version)
PYEOF
then
    echo "[ERRO] pyodbc nao esta funcional neste ambiente virtual."
    echo "       Verifique unixODBC e drivers ODBC instalados no servidor."
    exit 1
fi

echo "  [OK] Pre-requisitos PostgreSQL/ODBC verificados"
echo ""

# ===================================================================
# PASSO 5: Aplicar migracoes + inicializar dados (idempotente)
# ===================================================================
echo "[PASSO 5/5] Aplicando migracoes e inicializando dados..."
echo ""

export FLASK_APP=src/app.py
flask db upgrade

echo "  [OK] Migracoes aplicadas com sucesso"

python3 setup_init_data.py

echo ""

# ===================================================================
# CONCLUSAO
# ===================================================================
echo "==============================================================================="
echo " [OK] SETUP CONCLUIDO COM SUCESSO!"
echo "==============================================================================="
echo ""
echo "Proximas acoes:"
echo "  1. Execute  bash linux/run_local.sh    para modo local (localhost)"
echo "  2. Ou execute  bash linux/run_network.sh   para modo rede (Gunicorn)"
echo ""
echo "Acesso padrao:"
echo "  - Local: http://localhost:5000"
echo "  - Rede:  http://seu-ip-do-servidor:5000"
echo ""
echo "Credenciais padrao:"
echo "  - Usuario: pedro (ou outros usuarios criados)"
echo "  - Senha: 123456"
echo ""
echo "Para mais informacoes, ver: docs/INSTALLATION_GUIDE.md"
echo ""
