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
echo "  - Servidor: Waitress (performance)"
echo "  - Acesso:   Rede LAN (0.0.0.0:5000)"
echo "  - Porta:    5000"
echo "  - Debug:    OFF"
echo "  - Auto-desligamento: DESATIVADO"
echo ""
echo "==============================================================================="
echo ""

# ===================================================================
# Verificacao 1: Banco de dados
# ===================================================================
echo "[VERIFICACAO] Procurando banco de dados..."

if [ ! -f "instance/prontuario.db" ]; then
    echo ""
    echo "[ERRO] Banco de dados nao encontrado!"
    echo "       Arquivo esperado: instance/prontuario.db"
    echo ""
    echo "Solucao:"
    echo "  Execute primeiramente: bash linux/setup_linux.sh"
    echo ""
    exit 1
fi

echo "  [OK] Banco de dados encontrado"

# ===================================================================
# Verificacao 2: Arquivo de configuracao .env
# ===================================================================
echo "[VERIFICACAO] Procurando arquivo .env..."

if [ ! -f ".env" ]; then
    echo "  [AVISO] Arquivo .env nao encontrado. Criando com configuracoes padrao..."
    cat > .env << 'ENVEOF'
# =================================================================
# Patient Registration System - Configuracao do Ambiente
# Gerado automaticamente pelo run_network.sh
# =================================================================

SECRET_KEY=patient-reg-secret-key-2026-change-in-production
FLASK_ENV=production
FLASK_DEBUG=0
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DESKTOP_MODE=false
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
    echo "  [OK] Arquivo .env criado com configuracoes padrao"
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

export SERVER_HOST=0.0.0.0
export SERVER_PORT=5000
export DESKTOP_MODE=false
export FLASK_ENV=production
export FLASK_DEBUG=0

echo "  [OK] Variaveis configuradas"
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
# Abrir Navegador Automaticamente
# ===================================================================
echo "[NAVEGADOR] Abrindo http://localhost:$SERVER_PORT em 2 segundos..."
(sleep 2 && xdg-open "http://localhost:$SERVER_PORT" 2>/dev/null \
    || open "http://localhost:$SERVER_PORT" 2>/dev/null \
    || true) &

# ===================================================================
# Iniciar Servidor Waitress
# ===================================================================
waitress-serve --listen="$SERVER_HOST:$SERVER_PORT" wsgi:application

# Se chegou aqui, servidor foi encerrado
echo ""
echo "==============================================================================="
echo " Servidor encerrado"
echo "==============================================================================="
echo ""
