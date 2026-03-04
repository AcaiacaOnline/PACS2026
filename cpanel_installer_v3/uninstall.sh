#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Desinstalador v3.0
#============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           Planejamento Acaiaca - Desinstalador                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Diretório de instalação
DEFAULT_DIR="${HOME}/planejamento-acaiaca"
read -p "Diretório de instalação [$DEFAULT_DIR]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_DIR}

if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Diretório não encontrado: $INSTALL_DIR${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}ATENÇÃO: Esta ação irá:${NC}"
echo "  - Parar a aplicação"
echo "  - Remover todos os arquivos em $INSTALL_DIR"
echo "  - Remover configurações do proxy"
echo ""
echo -e "${RED}OS DADOS NÃO PODERÃO SER RECUPERADOS!${NC}"
echo ""

read -p "Deseja criar um backup antes? [S/n]: " DO_BACKUP
if [[ ! "$DO_BACKUP" =~ ^[Nn]$ ]]; then
    if [ -f "${INSTALL_DIR}/manage.sh" ]; then
        "${INSTALL_DIR}/manage.sh" backup
        echo ""
    fi
fi

read -p "Confirma a desinstalação? [s/N]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Ss]$ ]]; then
    echo "Desinstalação cancelada."
    exit 0
fi

echo ""
echo "Desinstalando..."

# Parar aplicação
if [ -f "${INSTALL_DIR}/manage.sh" ]; then
    "${INSTALL_DIR}/manage.sh" stop 2>/dev/null || true
fi

# Remover diretório
rm -rf "$INSTALL_DIR"

# Limpar public_html (se cPanel)
if [ -d "${HOME}/public_html" ]; then
    read -p "Remover arquivos do frontend em public_html? [s/N]: " REMOVE_PUBLIC
    if [[ "$REMOVE_PUBLIC" =~ ^[Ss]$ ]]; then
        rm -f "${HOME}/public_html/.htaccess"
        rm -f "${HOME}/public_html/index.html"
        rm -f "${HOME}/public_html/manifest.json"
        rm -f "${HOME}/public_html/service-worker.js"
        rm -rf "${HOME}/public_html/static"
        rm -rf "${HOME}/public_html/icons"
        echo "Arquivos do frontend removidos."
    fi
fi

echo ""
echo -e "${GREEN}Desinstalação concluída.${NC}"
echo ""
echo "Nota: O banco de dados (MongoDB/SQLite) NÃO foi removido."
echo "Para remover completamente, delete o banco manualmente."
