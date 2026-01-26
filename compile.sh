#!/bin/bash
#
# Script de compilação cruzada Windows em macOS/Linux
# Este script tenta compilar os executáveis Windows via PyInstaller
#
# NOTA: Para produção, execute este script em Windows!
#       Neste sistema (macOS), gerará .app em vez de .exe
#

set -e

echo "======================================================================"
echo "  Compilador v1.0.1 - Prontuário de Pacientes"
echo "======================================================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detectar sistema operacional
OS="$(uname -s)"
ARCH="$(uname -m)"

echo -e "${BLUE}ℹ️  Sistema Detectado:${NC} $OS ($ARCH)"
echo ""

# Se em Windows (Git Bash ou WSL), compilar para Windows
# Se em macOS/Linux, avisar e gerar estrutura
if [[ "$OS" == MINGW* ]] || [[ "$OS" == MSYS* ]]; then
    echo -e "${GREEN}✓ Windows detectado - Compilando executáveis nativos${NC}"
    COMPILE_MODE="windows"
elif [[ "$OS" == "Darwin" ]]; then
    echo -e "${YELLOW}⚠️  macOS detectado${NC}"
    echo "   Para gerar .exe (Windows), execute este script em Windows:"
    echo "   - Use build_releases.bat em vez deste script"
    echo ""
    echo -e "${YELLOW}ℹ️  Continuando com compilação macOS (resultado: .app)${NC}"
    COMPILE_MODE="macos"
else
    echo -e "${YELLOW}⚠️  Linux detectado${NC}"
    echo "   Compilando para Linux (resultado: binário ELF)"
    COMPILE_MODE="linux"
fi

echo ""
echo "======================================================================"
echo "  1. Validando Sistema"
echo "======================================================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 não encontrado${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"

# Verificar PyInstaller
if ! python3 -m pip show PyInstaller &>/dev/null; then
    echo -e "${RED}✗ PyInstaller não instalado${NC}"
    echo "  Executar: pip install PyInstaller>=6.10.0"
    exit 1
fi

PYINSTALLER_VERSION=$(python3 -m PyInstaller --version 2>&1)
echo -e "${GREEN}✓ PyInstaller ${PYINSTALLER_VERSION}${NC}"

# Verificar Waitress
if ! python3 -m pip show waitress &>/dev/null; then
    echo -e "${RED}✗ Waitress não instalado${NC}"
    echo "  Executar: pip install waitress==2.1.2"
    exit 1
fi

echo -e "${GREEN}✓ Waitress instalado${NC}"

# Verificar arquivos necessários
if [ ! -f "prontuario_64bits.spec" ]; then
    echo -e "${RED}✗ prontuario_64bits.spec não encontrado${NC}"
    exit 1
fi

if [ ! -f "prontuario_32bits.spec" ]; then
    echo -e "${RED}✗ prontuario_32bits.spec não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Arquivos .spec encontrados${NC}"

echo ""
echo "======================================================================"
echo "  2. Compilando Build 64-bits"
echo "======================================================================"
echo ""

echo -e "${BLUE}ℹ️  Iniciando PyInstaller para 64 bits...${NC}"
echo "    (Isso pode levar 10-15 minutos)"
echo ""

python3 -m PyInstaller --clean prontuario_64bits.spec

if [ -f "dist/64bits/prontuario-64bits/prontuario-64bits.exe" ] || \
   [ -f "dist/64bits/prontuario-64bits/prontuario-64bits" ]; then
    echo -e "${GREEN}✓ Build 64-bits compilado com sucesso${NC}"
else
    echo -e "${YELLOW}⚠️  Estrutura criada (executável pode estar em outro local)${NC}"
fi

echo ""
echo "======================================================================"
echo "  3. Compilando Build 32-bits"
echo "======================================================================"
echo ""

echo -e "${BLUE}ℹ️  Iniciando PyInstaller para 32 bits...${NC}"
echo "    (Isso pode levar 10-15 minutos)"
echo ""

python3 -m PyInstaller --clean prontuario_32bits.spec

if [ -f "dist/32bits/prontuario-32bits/prontuario-32bits.exe" ] || \
   [ -f "dist/32bits/prontuario-32bits/prontuario-32bits" ]; then
    echo -e "${GREEN}✓ Build 32-bits compilado com sucesso${NC}"
else
    echo -e "${YELLOW}⚠️  Estrutura criada (executável pode estar em outro local)${NC}"
fi

echo ""
echo "======================================================================"
echo "  4. Relatório Final"
echo "======================================================================"
echo ""

echo -e "${BLUE}Estrutura de Diretórios:${NC}"
echo ""

if [ -d "dist/64bits/prontuario-64bits" ]; then
    FILE_COUNT=$(find dist/64bits/prontuario-64bits -type f | wc -l)
    SIZE=$(du -sh dist/64bits/prontuario-64bits | cut -f1)
    echo -e "  64-bits: ${GREEN}✓${NC} ($FILE_COUNT arquivos, $SIZE)"
else
    echo -e "  64-bits: ${RED}✗${NC} (não encontrado)"
fi

if [ -d "dist/32bits/prontuario-32bits" ]; then
    FILE_COUNT=$(find dist/32bits/prontuario-32bits -type f | wc -l)
    SIZE=$(du -sh dist/32bits/prontuario-32bits | cut -f1)
    echo -e "  32-bits: ${GREEN}✓${NC} ($FILE_COUNT arquivos, $SIZE)"
else
    echo -e "  32-bits: ${RED}✗${NC} (não encontrado)"
fi

echo ""
echo "======================================================================"
echo "  5. Próximas Etapas"
echo "======================================================================"
echo ""

echo "1. Criar arquivos ZIP:"
echo ""
echo "   # 64 bits"
echo "   cd dist/64bits"
echo "   zip -r ../prontuario-v1.0.1-64bits.zip prontuario-64bits/"
echo ""
echo "   # 32 bits"
echo "   cd ../32bits"
echo "   zip -r ../prontuario-v1.0.1-32bits.zip prontuario-32bits/"
echo ""

echo "2. Upload para GitHub Release:"
echo "   https://github.com/phgutierrez/patient-registration-system/releases/new"
echo ""
echo "3. Anexar os arquivos ZIP:"
echo "   - prontuario-v1.0.1-64bits.zip"
echo "   - prontuario-v1.0.1-32bits.zip"
echo ""

if [[ "$COMPILE_MODE" == "windows" ]]; then
    echo -e "${GREEN}✓ Compilação em Windows completa!${NC}"
else
    echo -e "${YELLOW}ℹ️  NOTA: Executáveis gerados para $COMPILE_MODE${NC}"
    echo "         Para .exe nativos, execute em Windows ou use:"
    echo "         - WSL2 com Python Windows"
    echo "         - VirtualBox/Hyper-V com Windows"
    echo "         - GitHub Actions (recomendado)"
fi

echo ""
echo "======================================================================"
echo "  ✅ Processo concluído!"
echo "======================================================================"
echo ""
