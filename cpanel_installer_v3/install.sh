#!/bin/bash
#============================================================================
# Planejamento Acaiaca - Instalador cPanel v3.0
# Sistema de Gestão Municipal
# Compatível com: cPanel, Plesk, DirectAdmin, VPS
#============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Funções de log
log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

# Banner
clear
echo -e "${BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║     ____  _                  _                            _   ║
║    |  _ \| | __ _ _ __   ___(_) __ _ _ __ ___   ___ _ __ | |_ ║
║    | |_) | |/ _` | '_ \ / _ \ |/ _` | '_ ` _ \ / _ \ '_ \| __|║
║    |  __/| | (_| | | | |  __/ | (_| | | | | | |  __/ | | | |_ ║
║    |_|   |_|\__,_|_| |_|\___|_|\__,_|_| |_| |_|\___|_| |_|\__|║
║                                                               ║
║            ACAIACA - Sistema de Gestão Municipal v3.0         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Detectar sistema operacional
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        OS="CentOS/RHEL"
    else
        OS=$(uname -s)
    fi
    echo "$OS"
}

# Detectar painel de controle
detect_panel() {
    if [ -d "/usr/local/cpanel" ]; then
        echo "cpanel"
    elif [ -d "/usr/local/psa" ]; then
        echo "plesk"
    elif [ -d "/usr/local/directadmin" ]; then
        echo "directadmin"
    else
        echo "vps"
    fi
}

# Verificar requisitos
check_requirements() {
    log "Verificando requisitos do sistema..."
    
    # Python 3.8+
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [ "$(echo "$PYTHON_VERSION >= 3.8" | bc -l 2>/dev/null || echo 0)" -eq 1 ] || \
           [ "$(python3 -c 'import sys; print(1 if sys.version_info >= (3, 8) else 0)')" -eq 1 ]; then
            log "Python $PYTHON_VERSION encontrado"
        else
            error "Python 3.8+ necessário. Versão encontrada: $PYTHON_VERSION"
        fi
    else
        error "Python 3 não encontrado. Instale com: apt install python3 python3-pip python3-venv"
    fi
    
    # pip
    if ! command -v pip3 &> /dev/null; then
        warn "pip3 não encontrado. Tentando instalar..."
        python3 -m ensurepip --upgrade || error "Falha ao instalar pip"
    fi
    
    # Node.js (opcional, para rebuild do frontend)
    if command -v node &> /dev/null; then
        log "Node.js $(node -v) encontrado"
    else
        warn "Node.js não encontrado. Frontend será usado pré-compilado."
    fi
}

# Menu de configuração
show_menu() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                   CONFIGURAÇÃO DA INSTALAÇÃO                   ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Função principal de instalação
main() {
    OS=$(detect_os)
    PANEL=$(detect_panel)
    
    info "Sistema operacional: $OS"
    info "Painel detectado: $PANEL"
    echo ""
    
    check_requirements
    
    show_menu
    
    # Diretório de instalação
    if [ -n "$HOME" ]; then
        DEFAULT_DIR="${HOME}/planejamento-acaiaca"
    else
        DEFAULT_DIR="/var/www/planejamento-acaiaca"
    fi
    
    read -p "Diretório de instalação [$DEFAULT_DIR]: " INSTALL_DIR
    INSTALL_DIR=${INSTALL_DIR:-$DEFAULT_DIR}
    
    # Configuração do banco de dados
    echo ""
    echo -e "${YELLOW}Selecione o tipo de banco de dados:${NC}"
    echo "  1) MongoDB Atlas (Cloud - Recomendado para cPanel)"
    echo "  2) MongoDB Local"
    echo "  3) SQLite (Não requer servidor de banco)"
    echo ""
    read -p "Opção [1]: " DB_TYPE
    DB_TYPE=${DB_TYPE:-1}
    
    case $DB_TYPE in
        1)
            echo ""
            info "MongoDB Atlas selecionado"
            info "Crie um cluster gratuito em: https://www.mongodb.com/cloud/atlas"
            echo ""
            read -p "String de conexão MongoDB Atlas: " MONGO_URL
            if [ -z "$MONGO_URL" ]; then
                error "String de conexão obrigatória para MongoDB Atlas"
            fi
            DB_NAME="planejamento_acaiaca"
            ;;
        2)
            read -p "Host MongoDB [localhost]: " MONGO_HOST
            MONGO_HOST=${MONGO_HOST:-localhost}
            read -p "Porta MongoDB [27017]: " MONGO_PORT
            MONGO_PORT=${MONGO_PORT:-27017}
            read -p "Nome do banco [planejamento_acaiaca]: " DB_NAME
            DB_NAME=${DB_NAME:-planejamento_acaiaca}
            read -p "Usuário MongoDB (deixe vazio se não usar auth): " MONGO_USER
            if [ -n "$MONGO_USER" ]; then
                read -sp "Senha MongoDB: " MONGO_PASS
                echo ""
                MONGO_URL="mongodb://${MONGO_USER}:${MONGO_PASS}@${MONGO_HOST}:${MONGO_PORT}/${DB_NAME}?authSource=admin"
            else
                MONGO_URL="mongodb://${MONGO_HOST}:${MONGO_PORT}/${DB_NAME}"
            fi
            ;;
        3)
            info "SQLite selecionado (modo simplificado)"
            MONGO_URL="sqlite"
            DB_NAME="planejamento_acaiaca.db"
            warn "Nota: Algumas funcionalidades avançadas podem não estar disponíveis com SQLite"
            ;;
        *)
            error "Opção inválida"
            ;;
    esac
    
    # Domínio
    echo ""
    read -p "Domínio da aplicação (ex: sistema.seudominio.com.br): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        DOMAIN="localhost"
    fi
    
    # Porta do backend
    read -p "Porta do backend [8001]: " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-8001}
    
    # Confirmação
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                    RESUMO DA CONFIGURAÇÃO                      ${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Diretório: $INSTALL_DIR"
    echo "  Banco de dados: $([ "$DB_TYPE" = "3" ] && echo "SQLite" || echo "MongoDB")"
    echo "  Domínio: $DOMAIN"
    echo "  Porta backend: $BACKEND_PORT"
    echo ""
    
    read -p "Confirma a instalação? [S/n]: " CONFIRM
    if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
        echo "Instalação cancelada."
        exit 0
    fi
    
    # Executar instalação
    do_install
}

# Função de instalação
do_install() {
    log "Iniciando instalação..."
    
    # Criar estrutura de diretórios
    log "Criando estrutura de diretórios..."
    mkdir -p "${INSTALL_DIR}"/{backend,frontend,logs,uploads/mrosc,backups}
    
    # Copiar arquivos
    log "Copiando arquivos..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ -d "${SCRIPT_DIR}/backend" ]; then
        cp -r "${SCRIPT_DIR}/backend/"* "${INSTALL_DIR}/backend/"
    else
        error "Diretório backend não encontrado. Execute o build.sh primeiro."
    fi
    
    if [ -d "${SCRIPT_DIR}/frontend/build" ]; then
        cp -r "${SCRIPT_DIR}/frontend/build/"* "${INSTALL_DIR}/frontend/"
    else
        error "Build do frontend não encontrado. Execute o build.sh primeiro."
    fi
    
    # Criar ambiente virtual Python
    log "Criando ambiente virtual Python..."
    cd "${INSTALL_DIR}/backend"
    python3 -m venv venv
    source venv/bin/activate
    
    # Instalar dependências
    log "Instalando dependências Python..."
    pip install --upgrade pip wheel setuptools
    pip install -r requirements.txt
    
    deactivate
    
    # Criar arquivo .env
    log "Configurando variáveis de ambiente..."
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    cat > "${INSTALL_DIR}/backend/.env" << EOF
# Planejamento Acaiaca - Configuração
# Gerado em: $(date)

# Banco de Dados
MONGO_URL=${MONGO_URL}
DB_NAME=${DB_NAME}

# JWT
JWT_SECRET=${JWT_SECRET}
JWT_EXPIRATION_DAYS=7

# Servidor
HOST=0.0.0.0
PORT=${BACKEND_PORT}

# Ambiente
ENVIRONMENT=production
DEBUG=false

# Domínio
DOMAIN=${DOMAIN}
FRONTEND_URL=https://${DOMAIN}

# Email (configurar manualmente)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=noreply@${DOMAIN}
EOF
    
    chmod 600 "${INSTALL_DIR}/backend/.env"
    
    # Criar scripts de gerenciamento
    create_management_scripts
    
    # Configurar proxy reverso baseado no painel
    configure_proxy
    
    # Iniciar aplicação
    log "Iniciando aplicação..."
    "${INSTALL_DIR}/manage.sh" start
    
    # Verificar status
    sleep 3
    if "${INSTALL_DIR}/manage.sh" status | grep -q "Rodando"; then
        show_success
    else
        warn "Aplicação pode não ter iniciado corretamente"
        warn "Verifique os logs em: ${INSTALL_DIR}/logs/"
    fi
}

# Criar scripts de gerenciamento
create_management_scripts() {
    log "Criando scripts de gerenciamento..."
    
    cat > "${INSTALL_DIR}/manage.sh" << 'MANAGE_EOF'
#!/bin/bash
# Planejamento Acaiaca - Gerenciamento

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
PID_FILE="${SCRIPT_DIR}/app.pid"
LOG_FILE="${SCRIPT_DIR}/logs/app.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Aplicação já está rodando (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    echo "Iniciando aplicação..."
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Carregar .env
    export $(grep -v '^#' .env | xargs)
    
    nohup python3 -m uvicorn server:app \
        --host ${HOST:-0.0.0.0} \
        --port ${PORT:-8001} \
        --workers 2 \
        --log-level info \
        > "$LOG_FILE" 2>&1 &
    
    echo $! > "$PID_FILE"
    sleep 2
    
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Aplicação iniciada com sucesso (PID: $(cat $PID_FILE))"
        echo "Acesse: https://${DOMAIN:-localhost}"
    else
        echo "Falha ao iniciar a aplicação. Verifique os logs."
        rm -f "$PID_FILE"
        return 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "Parando aplicação (PID: $PID)..."
            kill $PID
            sleep 2
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID
            fi
        fi
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
        echo "Aplicação: Rodando (PID: $(cat $PID_FILE))"
        # Verificar se a API responde
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT:-8001}/api/health | grep -q "200"; then
            echo "API: Saudável"
        else
            echo "API: Não responde"
        fi
    else
        echo "Aplicação: Parada"
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "Arquivo de log não encontrado"
    fi
}

backup() {
    BACKUP_DIR="${SCRIPT_DIR}/backups"
    BACKUP_FILE="${BACKUP_DIR}/backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    echo "Criando backup..."
    mkdir -p "$BACKUP_DIR"
    
    tar -czf "$BACKUP_FILE" \
        -C "$SCRIPT_DIR" \
        backend/.env \
        uploads \
        logs \
        2>/dev/null
    
    echo "Backup criado: $BACKUP_FILE"
    
    # Manter apenas os últimos 7 backups
    ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm
}

case "$1" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    logs)    logs ;;
    backup)  backup ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs|backup}"
        exit 1
        ;;
esac
MANAGE_EOF
    
    chmod +x "${INSTALL_DIR}/manage.sh"
}

# Configurar proxy reverso
configure_proxy() {
    log "Configurando proxy reverso..."
    
    case $PANEL in
        cpanel)
            configure_cpanel_proxy
            ;;
        plesk)
            configure_plesk_proxy
            ;;
        *)
            configure_generic_proxy
            ;;
    esac
}

# Configuração para cPanel
configure_cpanel_proxy() {
    PUBLIC_HTML="${HOME}/public_html"
    
    # Copiar frontend para public_html
    log "Publicando frontend em public_html..."
    cp -r "${INSTALL_DIR}/frontend/"* "${PUBLIC_HTML}/"
    
    # Criar .htaccess
    cat > "${PUBLIC_HTML}/.htaccess" << 'HTACCESS_EOF'
# Planejamento Acaiaca - Proxy Reverso cPanel

RewriteEngine On

# Forçar HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Proxy para API
RewriteCond %{REQUEST_URI} ^/api/(.*)$
RewriteRule ^api/(.*)$ http://127.0.0.1:8001/api/$1 [P,L]

# SPA Fallback - Redirecionar todas as rotas para index.html
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /index.html [L]

# Headers de segurança
<IfModule mod_headers.c>
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>

# Cache de arquivos estáticos
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/png "access plus 1 month"
    ExpiresByType image/jpeg "access plus 1 month"
    ExpiresByType image/gif "access plus 1 month"
    ExpiresByType text/css "access plus 1 week"
    ExpiresByType application/javascript "access plus 1 week"
</IfModule>

# Compressão
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/css application/javascript application/json
</IfModule>
HTACCESS_EOF
    
    log "Configuração cPanel concluída"
    warn "IMPORTANTE: Ative o módulo mod_proxy no cPanel se ainda não estiver ativo"
}

# Configuração genérica (Nginx/Apache)
configure_generic_proxy() {
    # Criar exemplo de configuração Nginx
    cat > "${INSTALL_DIR}/nginx.conf.example" << 'NGINX_EOF'
# Planejamento Acaiaca - Configuração Nginx

server {
    listen 80;
    server_name SEU_DOMINIO;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name SEU_DOMINIO;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    root /path/to/planejamento-acaiaca/frontend;
    index index.html;

    # API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Frontend SPA
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache de estáticos
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF
    
    info "Configuração de exemplo Nginx criada em: ${INSTALL_DIR}/nginx.conf.example"
}

# Configuração para Plesk
configure_plesk_proxy() {
    info "Para Plesk, configure o proxy reverso através do painel:"
    info "1. Vá em 'Apache & nginx Settings'"
    info "2. Adicione em 'Additional nginx directives':"
    info ""
    echo "   location /api/ {"
    echo "       proxy_pass http://127.0.0.1:${BACKEND_PORT};"
    echo "   }"
    
    configure_generic_proxy
}

# Mensagem de sucesso
show_success() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           INSTALAÇÃO CONCLUÍDA COM SUCESSO!                    ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}URL:${NC} https://${DOMAIN}"
    echo ""
    echo -e "  ${CYAN}Comandos de gerenciamento:${NC}"
    echo "    ${INSTALL_DIR}/manage.sh start   - Iniciar"
    echo "    ${INSTALL_DIR}/manage.sh stop    - Parar"
    echo "    ${INSTALL_DIR}/manage.sh restart - Reiniciar"
    echo "    ${INSTALL_DIR}/manage.sh status  - Status"
    echo "    ${INSTALL_DIR}/manage.sh logs    - Ver logs"
    echo "    ${INSTALL_DIR}/manage.sh backup  - Criar backup"
    echo ""
    echo -e "  ${CYAN}Credenciais padrão:${NC}"
    echo "    Email: admin@${DOMAIN}"
    echo "    Senha: (definida no primeiro acesso)"
    echo ""
    echo -e "  ${CYAN}Configurações:${NC}"
    echo "    Backend .env: ${INSTALL_DIR}/backend/.env"
    echo "    Logs: ${INSTALL_DIR}/logs/"
    echo ""
    echo -e "${YELLOW}IMPORTANTE:${NC}"
    echo "  1. Configure o cron job para manutenção:"
    echo "     0 2 * * * ${INSTALL_DIR}/manage.sh backup"
    echo ""
    echo "  2. Configure o email SMTP em: ${INSTALL_DIR}/backend/.env"
    echo ""
}

# Executar
main "$@"
