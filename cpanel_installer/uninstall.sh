#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Desinstalador cPanel
#============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INSTALL_DIR="${HOME}/planejamento-acaiaca"

echo -e "${YELLOW}"
echo "=============================================="
echo "   Planejamento Acaiaca - Desinstalador"
echo "=============================================="
echo -e "${NC}"

read -p "Tem certeza que deseja desinstalar? (s/N): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo "Desinstalação cancelada."
    exit 0
fi

# Parar aplicação
if [ -f "${INSTALL_DIR}/manage.sh" ]; then
    echo "Parando aplicação..."
    "${INSTALL_DIR}/manage.sh" stop 2>/dev/null || true
fi

# Remover diretórios
echo "Removendo arquivos..."
rm -rf "${INSTALL_DIR}"

# Limpar public_html (cuidado!)
read -p "Remover arquivos do public_html? (s/N): " clean_public
if [ "$clean_public" = "s" ] || [ "$clean_public" = "S" ]; then
    rm -rf "${HOME}/public_html/"*
fi

echo -e "${GREEN}Desinstalação concluída!${NC}"
