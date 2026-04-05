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
echo "  - Servidor: Waitress (performance)"
echo "  - Acesso:   http://localhost:5000 (localhost apenas)"
echo "  - Porta:    5000"
echo "  - Debug:    OFF"
echo "  - Auto-desligamento: ATIVADO"
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
    echo "  [AVISO] Arquivo .env nao encontrado. Copiando template canonico .env.example..."
    cp .env.example .env
    echo "  [OK] Arquivo .env criado a partir de .env.example"
    echo "  [AVISO] Revise ADMIN_BOOTSTRAP_* e integracoes opcionais antes do primeiro acesso"
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
export DESKTOP_MODE=true
export FLASK_ENV=production
export FLASK_DEBUG=0

echo "  [OK] Variaveis configuradas"
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
# Iniciar Servidor Waitress
# ===================================================================
waitress-serve --listen="$SERVER_HOST:$SERVER_PORT" wsgi:application

# Se chegou aqui, servidor foi encerrado
echo ""
echo "==============================================================================="
echo " Servidor encerrado"
echo "==============================================================================="
echo ""
