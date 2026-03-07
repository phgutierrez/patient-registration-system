#!/bin/bash
# ===============================================================================
# RUN NETWORK - Patient Registration System
# Executa o sistema no modo REDE (LAN hospitalar/multi-usuario)
# ===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "==============================================================================="
echo " INICIANDO - Modo REDE (LAN/Multi-usuario)"
echo "==============================================================================="
echo ""
echo "Configuracao:"
echo "  - Servidor: Gunicorn (producao Linux)"
echo "  - Acesso:   Rede LAN (0.0.0.0:5000)"
echo "  - Porta:    5000"
echo "  - Debug:    OFF"
echo "  - Auto-desligamento: DESATIVADO"
echo ""
echo "==============================================================================="
echo ""

# ===================================================================
# Verificacao 1: Arquivo de configuracao .env
# ===================================================================
echo "[VERIFICACAO] Procurando arquivo .env..."

if [ ! -f ".env" ]; then
    echo "[ERRO] Arquivo .env nao encontrado!"
    echo "       Execute primeiro: bash linux/setup_linux.sh"
    exit 1
fi

echo "  [OK] Arquivo .env encontrado"

DEFAULT_SECRET_KEY="patient-reg-secret-key-2026-change-in-production"
SECRET_KEY_VALUE="$(grep -E '^SECRET_KEY=' .env | tail -n 1 | cut -d '=' -f2-)"
DATABASE_URL_VALUE="$(grep -E '^DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2-)"

if [ -z "$SECRET_KEY_VALUE" ] || [ "$SECRET_KEY_VALUE" = "$DEFAULT_SECRET_KEY" ]; then
    echo "[ERRO] SECRET_KEY invalido no .env. Defina uma chave unica antes de iniciar em rede."
    exit 1
fi

if [ -z "$DATABASE_URL_VALUE" ] || [[ "$DATABASE_URL_VALUE" != postgresql* ]]; then
    echo "[ERRO] DATABASE_URL invalido no .env. Em rede Linux use PostgreSQL."
    echo "       Exemplo: DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/database"
    exit 1
fi

# ===================================================================
# Verificacao 3: Ambiente virtual
# ===================================================================
echo "[VERIFICACAO] Procurando ambiente virtual..."

if [ ! -f ".venv/bin/activate" ]; then
    echo ""
    echo "[ERRO] Ambiente virtual nao encontrado!"
    echo "       Diretorio esperado: .venv/"
    echo ""
    echo "Solucao:"
    echo "  Execute: bash linux/setup_linux.sh"
    echo ""
    exit 1
fi

echo "  [OK] Ambiente virtual encontrado"
echo ""

# ===================================================================
# Ativar Ambiente Virtual
# ===================================================================
echo "[CONFIGURACAO] Ativando ambiente virtual..."

# shellcheck disable=SC1091
source .venv/bin/activate

echo "  [OK] Ambiente virtual ativado"
echo ""

# ===================================================================
# Configurar Variaveis de Ambiente
# ===================================================================
echo "[CONFIGURACAO] Definindo variaveis de ambiente..."

export SERVER_HOST=0.0.0.0
export SERVER_PORT=5000
export DESKTOP_MODE=false
export FLASK_ENV=production
export FLASK_DEBUG=0
export GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
export GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"

echo "  [OK] Variaveis configuradas"
echo ""

# ===================================================================
# Verificacao 4: Conectividade com banco configurado
# ===================================================================
echo "[VERIFICACAO] Testando conectividade com banco de dados..."

if ! python3 - << 'PYEOF'
from src.app import create_app
from src.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.session.execute(text('SELECT 1'))

print('ok')
PYEOF
then
    echo "[ERRO] Falha ao conectar no banco de dados configurado."
    echo "       Verifique DATABASE_URL no .env e acesso ao PostgreSQL."
    exit 1
fi

echo "  [OK] Banco de dados acessivel"
echo ""

# ===================================================================
# Obter IP Local
# ===================================================================
echo "[CONFIGURACAO] Detectando endereco IP local..."

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP" ]; then
    IP="consulte: ip addr"
fi

echo "  [OK] IP local detectado: $IP"
echo ""

# ===================================================================
# Mensagem Final e Inicializacao
# ===================================================================
echo "==============================================================================="
echo " SERVIDOR DE REDE INICIANDO"
echo "==============================================================================="
echo ""
echo "Acesso:"
echo "  - Local (este computador):    http://localhost:$SERVER_PORT"
echo "  - Rede (outros computadores): http://$IP:$SERVER_PORT"
echo ""
echo "Parar o servidor: Pressione CTRL+C"
echo ""
echo "==============================================================================="
echo ""

# ===================================================================
# Iniciar Servidor Gunicorn
# ===================================================================
gunicorn \
    --bind "$SERVER_HOST:$SERVER_PORT" \
    --workers "$GUNICORN_WORKERS" \
    --timeout "$GUNICORN_TIMEOUT" \
    --worker-tmp-dir /dev/shm \
    wsgi:application

# Se chegou aqui, servidor foi encerrado
echo ""
echo "==============================================================================="
echo " Servidor encerrado"
echo "==============================================================================="
echo ""
