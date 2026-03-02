#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Script de Build para cPanel
# Gera o pacote de instalação completo
#============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${BLUE}"
echo "=============================================="
echo "   Planejamento Acaiaca - Build cPanel"
echo "=============================================="
echo -e "${NC}"

# Diretórios
ROOT_DIR="/app"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
BUILD_DIR="${ROOT_DIR}/cpanel_build"
OUTPUT_DIR="${ROOT_DIR}/cpanel_installer"

# Versão
VERSION="2.0.0"
DATE=$(date +%Y%m%d)

# Limpar build anterior
log "Limpando build anterior..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/backend"
mkdir -p "${BUILD_DIR}/frontend"

# ==================== BACKEND ====================
log "Preparando backend..."

# Copiar arquivos essenciais
cp "${BACKEND_DIR}/server.py" "${BUILD_DIR}/backend/"
cp "${BACKEND_DIR}/requirements.txt" "${BUILD_DIR}/backend/"
cp "${BACKEND_DIR}/create_indexes.py" "${BUILD_DIR}/backend/"
cp -r "${BACKEND_DIR}/models" "${BUILD_DIR}/backend/"
cp -r "${BACKEND_DIR}/routes" "${BUILD_DIR}/backend/"
cp -r "${BACKEND_DIR}/utils" "${BUILD_DIR}/backend/"
cp -r "${BACKEND_DIR}/services" "${BUILD_DIR}/backend/"
cp -r "${BACKEND_DIR}/middleware" "${BUILD_DIR}/backend/" 2>/dev/null || mkdir -p "${BUILD_DIR}/backend/middleware"
cp -r "${BACKEND_DIR}/static" "${BUILD_DIR}/backend/"

# Copiar assets
mkdir -p "${BUILD_DIR}/backend/assets"
cp "${BACKEND_DIR}/static/brasao_acaiaca.png" "${BUILD_DIR}/backend/assets/" 2>/dev/null || true

# Criar diretórios necessários
mkdir -p "${BUILD_DIR}/backend/logs"
mkdir -p "${BUILD_DIR}/backend/uploads/mrosc"

# Remover arquivos desnecessários
find "${BUILD_DIR}/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "${BUILD_DIR}/backend" -name "*.pyc" -delete 2>/dev/null || true
find "${BUILD_DIR}/backend" -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

# ==================== FRONTEND ====================
log "Preparando frontend..."

cd "${FRONTEND_DIR}"

# Build de produção
log "Executando build do React..."
export NODE_ENV=production
yarn build

# Copiar build
cp -r "${FRONTEND_DIR}/build" "${BUILD_DIR}/frontend/"

# ==================== INSTALADOR ====================
log "Preparando instalador..."

# Copiar scripts de instalação
cp "${OUTPUT_DIR}/install.sh" "${BUILD_DIR}/"
cp "${OUTPUT_DIR}/uninstall.sh" "${BUILD_DIR}/"
cp "${OUTPUT_DIR}/README.md" "${BUILD_DIR}/"

# Tornar scripts executáveis
chmod +x "${BUILD_DIR}/install.sh"
chmod +x "${BUILD_DIR}/uninstall.sh"

# ==================== PACOTE FINAL ====================
log "Gerando pacote..."

cd "${ROOT_DIR}"
PACKAGE_NAME="planejamento-acaiaca-cpanel-v${VERSION}-${DATE}.zip"

# Criar ZIP
cd "${BUILD_DIR}"
zip -r "${ROOT_DIR}/${PACKAGE_NAME}" .

# Calcular checksum
cd "${ROOT_DIR}"
sha256sum "${PACKAGE_NAME}" > "${PACKAGE_NAME}.sha256"

# Estatísticas
PACKAGE_SIZE=$(du -h "${PACKAGE_NAME}" | cut -f1)

echo ""
echo -e "${GREEN}=============================================="
echo "   Build concluído com sucesso!"
echo "=============================================="
echo -e "${NC}"
echo ""
echo "📦 Pacote: ${PACKAGE_NAME}"
echo "📊 Tamanho: ${PACKAGE_SIZE}"
echo "🔑 Checksum: ${PACKAGE_NAME}.sha256"
echo ""
echo "Para instalar no cPanel:"
echo "  1. Faça upload do arquivo .zip para o servidor"
echo "  2. Extraia: unzip ${PACKAGE_NAME}"
echo "  3. Execute: ./install.sh db_name db_user db_pass dominio"
echo ""

# Limpar diretório de build temporário
rm -rf "${BUILD_DIR}"

log "Build finalizado!"
