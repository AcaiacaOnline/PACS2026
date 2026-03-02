#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Instalador cPanel
# Sistema de Gestão Municipal
# Versão: 2.0.0
# Data: 2026-02-06
#============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função de log
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Banner
echo -e "${BLUE}"
echo "=============================================="
echo "   Planejamento Acaiaca - Instalador cPanel"
echo "   Sistema de Gestão Municipal v2.0"
echo "=============================================="
echo -e "${NC}"

# Verificar se está rodando como usuário correto
if [ -z "$HOME" ]; then
    error "Variável HOME não definida"
fi

# Diretório de instalação
INSTALL_DIR="${HOME}/planejamento-acaiaca"
BACKEND_DIR="${INSTALL_DIR}/backend"
FRONTEND_DIR="${INSTALL_DIR}/frontend"
PUBLIC_HTML="${HOME}/public_html"

# Verificar argumentos
DB_NAME="${1:-planejamento_acaiaca}"
DB_USER="${2:-}"
DB_PASS="${3:-}"
DOMAIN="${4:-}"

if [ -z "$DB_USER" ] || [ -z "$DB_PASS" ]; then
    echo ""
    echo "Uso: ./install.sh <db_name> <db_user> <db_password> [domain]"
    echo ""
    echo "Parâmetros:"
    echo "  db_name     - Nome do banco MongoDB (padrão: planejamento_acaiaca)"
    echo "  db_user     - Usuário do banco de dados"
    echo "  db_password - Senha do banco de dados"
    echo "  domain      - Domínio da aplicação (opcional)"
    echo ""
    error "Parâmetros obrigatórios não fornecidos"
fi

log "Iniciando instalação..."
log "Diretório: ${INSTALL_DIR}"
log "Banco de dados: ${DB_NAME}"

# Criar estrutura de diretórios
log "Criando estrutura de diretórios..."
mkdir -p "${INSTALL_DIR}"
mkdir -p "${BACKEND_DIR}/logs"
mkdir -p "${BACKEND_DIR}/uploads/mrosc"
mkdir -p "${BACKEND_DIR}/static"
mkdir -p "${FRONTEND_DIR}/build"

# Copiar arquivos do backend
log "Copiando arquivos do backend..."
cp -r ./backend/* "${BACKEND_DIR}/"

# Copiar arquivos do frontend (build)
log "Copiando arquivos do frontend..."
cp -r ./frontend/build/* "${FRONTEND_DIR}/build/"

# Criar arquivo .env do backend
log "Configurando variáveis de ambiente..."
cat > "${BACKEND_DIR}/.env" << EOF
# Planejamento Acaiaca - Configuração de Ambiente
# Gerado automaticamente pelo instalador

# MongoDB
MONGO_URL=mongodb://${DB_USER}:${DB_PASS}@localhost:27017/${DB_NAME}?authSource=admin
DB_NAME=${DB_NAME}

# JWT
JWT_SECRET=$(openssl rand -hex 32)
JWT_EXPIRATION_DAYS=7

# Servidor
HOST=0.0.0.0
PORT=8001

# Ambiente
ENVIRONMENT=production
DEBUG=false

# Email (configurar manualmente)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=

# Domínio
DOMAIN=${DOMAIN:-localhost}
EOF

# Criar arquivo .env do frontend
cat > "${FRONTEND_DIR}/.env" << EOF
REACT_APP_BACKEND_URL=https://${DOMAIN:-localhost}/api
EOF

# Criar script de inicialização do backend
log "Criando scripts de inicialização..."
cat > "${BACKEND_DIR}/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
exec uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
EOF
chmod +x "${BACKEND_DIR}/start.sh"

# Criar ambiente virtual Python
log "Criando ambiente virtual Python..."
cd "${BACKEND_DIR}"
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
log "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Desativar venv
deactivate

# Configurar .htaccess para proxy reverso
log "Configurando proxy reverso..."
cat > "${PUBLIC_HTML}/.htaccess" << 'EOF'
# Planejamento Acaiaca - Proxy Reverso
RewriteEngine On

# Redirecionar requisições da API para o backend
RewriteCond %{REQUEST_URI} ^/api/(.*)$
RewriteRule ^api/(.*)$ http://127.0.0.1:8001/api/$1 [P,L]

# Servir arquivos estáticos do frontend
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /index.html [L]
EOF

# Copiar build do frontend para public_html
log "Publicando frontend..."
cp -r "${FRONTEND_DIR}/build/"* "${PUBLIC_HTML}/"

# Criar script de gerenciamento
cat > "${INSTALL_DIR}/manage.sh" << 'EOF'
#!/bin/bash
# Planejamento Acaiaca - Script de Gerenciamento

BACKEND_DIR="$(dirname "$0")/backend"
PID_FILE="${BACKEND_DIR}/app.pid"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Aplicação já está rodando (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2 > logs/app.log 2>&1 &
    echo $! > "$PID_FILE"
    echo "Aplicação iniciada (PID: $(cat $PID_FILE))"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        kill $(cat "$PID_FILE") 2>/dev/null
        rm -f "$PID_FILE"
        echo "Aplicação parada"
    else
        echo "Aplicação não está rodando"
    fi
}

restart() {
    stop
    sleep 2
    start
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Aplicação rodando (PID: $(cat $PID_FILE))"
    else
        echo "Aplicação parada"
    fi
}

logs() {
    tail -f "${BACKEND_DIR}/logs/app.log"
}

case "$1" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF
chmod +x "${INSTALL_DIR}/manage.sh"

# Configurar permissões
log "Configurando permissões..."
chmod -R 755 "${INSTALL_DIR}"
chmod -R 777 "${BACKEND_DIR}/logs"
chmod -R 777 "${BACKEND_DIR}/uploads"
chmod 600 "${BACKEND_DIR}/.env"

# Iniciar aplicação
log "Iniciando aplicação..."
"${INSTALL_DIR}/manage.sh" start

# Verificar se está rodando
sleep 3
if "${INSTALL_DIR}/manage.sh" status | grep -q "rodando"; then
    echo ""
    echo -e "${GREEN}=============================================="
    echo "   Instalação concluída com sucesso!"
    echo "=============================================="
    echo -e "${NC}"
    echo ""
    echo "Acesse sua aplicação em: https://${DOMAIN:-seu-dominio.com}"
    echo ""
    echo "Comandos úteis:"
    echo "  ${INSTALL_DIR}/manage.sh start   - Iniciar aplicação"
    echo "  ${INSTALL_DIR}/manage.sh stop    - Parar aplicação"
    echo "  ${INSTALL_DIR}/manage.sh restart - Reiniciar aplicação"
    echo "  ${INSTALL_DIR}/manage.sh status  - Verificar status"
    echo "  ${INSTALL_DIR}/manage.sh logs    - Ver logs em tempo real"
    echo ""
else
    warn "Aplicação pode não ter iniciado corretamente."
    warn "Verifique os logs em: ${BACKEND_DIR}/logs/"
fi

log "Instalação finalizada!"
