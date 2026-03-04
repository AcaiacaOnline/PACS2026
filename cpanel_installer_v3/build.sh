#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Build Script v3.0
# Gera pacote de instalação completo
#============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║        Planejamento Acaiaca - Build de Instalação v3.0        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${SCRIPT_DIR}/dist"
VERSION="3.0.0"
PACKAGE_NAME="planejamento-acaiaca-v${VERSION}"

# Limpar build anterior
log "Limpando build anterior..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/${PACKAGE_NAME}"/{backend,frontend}

# Build do Frontend
log "Construindo frontend..."
cd "${PROJECT_ROOT}/frontend"

if [ ! -d "node_modules" ]; then
    log "Instalando dependências do frontend..."
    yarn install --frozen-lockfile
fi

log "Gerando build de produção..."
REACT_APP_BACKEND_URL="" yarn build

# Copiar build do frontend
log "Copiando frontend..."
cp -r build/* "${BUILD_DIR}/${PACKAGE_NAME}/frontend/"

# Copiar backend
log "Copiando backend..."
cd "${PROJECT_ROOT}/backend"

# Arquivos essenciais do backend
cp server.py "${BUILD_DIR}/${PACKAGE_NAME}/backend/"
cp requirements.txt "${BUILD_DIR}/${PACKAGE_NAME}/backend/"
cp -r models "${BUILD_DIR}/${PACKAGE_NAME}/backend/" 2>/dev/null || mkdir -p "${BUILD_DIR}/${PACKAGE_NAME}/backend/models"
cp -r routes "${BUILD_DIR}/${PACKAGE_NAME}/backend/" 2>/dev/null || mkdir -p "${BUILD_DIR}/${PACKAGE_NAME}/backend/routes"
cp -r middleware "${BUILD_DIR}/${PACKAGE_NAME}/backend/" 2>/dev/null || mkdir -p "${BUILD_DIR}/${PACKAGE_NAME}/backend/middleware"

# Criar estrutura de diretórios necessária
mkdir -p "${BUILD_DIR}/${PACKAGE_NAME}/backend"/{logs,uploads/mrosc,static}

# Copiar scripts de instalação
log "Copiando scripts de instalação..."
cp "${SCRIPT_DIR}/install.sh" "${BUILD_DIR}/${PACKAGE_NAME}/"
cp "${SCRIPT_DIR}/uninstall.sh" "${BUILD_DIR}/${PACKAGE_NAME}/" 2>/dev/null || true
cp -r "${SCRIPT_DIR}/docs" "${BUILD_DIR}/${PACKAGE_NAME}/" 2>/dev/null || mkdir -p "${BUILD_DIR}/${PACKAGE_NAME}/docs"

# Criar README
cat > "${BUILD_DIR}/${PACKAGE_NAME}/README.md" << 'EOF'
# Planejamento Acaiaca - Sistema de Gestão Municipal v3.0

## Requisitos

### Mínimos
- Python 3.8+
- 512MB RAM
- 1GB espaço em disco

### Recomendados
- Python 3.10+
- 1GB RAM
- 2GB espaço em disco
- MongoDB Atlas ou MongoDB 4.4+

## Instalação Rápida

```bash
# 1. Extrair o pacote
unzip planejamento-acaiaca-v3.0.0.zip
cd planejamento-acaiaca-v3.0.0

# 2. Executar instalador
chmod +x install.sh
./install.sh
```

## Opções de Banco de Dados

### MongoDB Atlas (Recomendado para cPanel)
1. Crie uma conta gratuita em: https://www.mongodb.com/cloud/atlas
2. Crie um cluster (M0 gratuito é suficiente)
3. Obtenha a string de conexão
4. Use no instalador quando solicitado

### MongoDB Local
- Instale MongoDB no servidor
- O instalador configurará automaticamente

### SQLite (Simplificado)
- Não requer servidor de banco externo
- Recomendado para testes ou pequenas instalações

## Comandos de Gerenciamento

```bash
# Iniciar
./manage.sh start

# Parar
./manage.sh stop

# Reiniciar
./manage.sh restart

# Ver status
./manage.sh status

# Ver logs
./manage.sh logs

# Criar backup
./manage.sh backup
```

## Configuração de Email

Edite o arquivo `backend/.env`:

```env
SMTP_HOST=smtp.seuservidor.com
SMTP_PORT=587
SMTP_USER=seu@email.com
SMTP_PASS=suasenha
```

## Suporte

- Documentação: docs/
- GitHub: https://github.com/prefeitura-acaiaca/planejamento

## Licença

Proprietário - Prefeitura Municipal de Acaiaca/MG
EOF

# Criar pacote
log "Criando pacote de distribuição..."
cd "${BUILD_DIR}"
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
zip -rq "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}"

# Calcular checksums
log "Calculando checksums..."
sha256sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.tar.gz.sha256"
sha256sum "${PACKAGE_NAME}.zip" > "${PACKAGE_NAME}.zip.sha256"

# Limpar diretório temporário
rm -rf "${BUILD_DIR}/${PACKAGE_NAME}"

# Resultado
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    BUILD CONCLUÍDO!                            ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Pacotes gerados em: ${BUILD_DIR}"
echo ""
ls -lh "${BUILD_DIR}"
echo ""
echo "Para distribuir, envie um dos arquivos:"
echo "  - ${PACKAGE_NAME}.tar.gz (Linux/Mac)"
echo "  - ${PACKAGE_NAME}.zip (Windows/Universal)"
