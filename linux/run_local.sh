#!/bin/bash
# ===============================================================================
# RUN LOCAL - Patient Registration System
# Executa o sistema no modo LOCAL (desenvolvimento/desktop)
# ===============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "==============================================================================="
echo " INICIANDO - Modo LOCAL (Desktop)"
echo "==============================================================================="
echo ""
echo "Configuracao:"
echo "  - Servidor: Gunicorn"
echo "  - Acesso:   http://localhost:5000 (localhost apenas)"
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

export SERVER_HOST=127.0.0.1
export SERVER_PORT=5000
export DESKTOP_MODE=false
export FLASK_ENV=production
export FLASK_DEBUG=0
export GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"
export GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"

echo "  [OK] Variaveis configuradas"
echo ""

# ===================================================================
# Verificacao 3: Conectividade com banco configurado
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
# Mensagem Final e Inicializacao
# ===================================================================
echo "==============================================================================="
echo " SERVIDOR LOCAL INICIANDO"
echo "==============================================================================="
echo ""
echo "Acesso:"
echo "  - Local: http://localhost:$SERVER_PORT"
echo ""
echo "Parar o servidor: Pressione CTRL+C"
echo ""
echo "==============================================================================="
echo ""

# ===================================================================
# Abrir Navegador Automaticamente
# ===================================================================
echo "[NAVEGADOR] Abrindo http://localhost:$SERVER_PORT em 2 segundos..."
(sleep 2 && xdg-open "http://localhost:$SERVER_PORT" 2>/dev/null \
    || open "http://localhost:$SERVER_PORT" 2>/dev/null \
    || true) &

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
