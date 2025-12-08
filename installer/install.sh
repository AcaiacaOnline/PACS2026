#!/bin/bash

# PAC Acaiaca 2026 - Script de Instalação Automática
# Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística

set -e

echo "=============================================="
echo "   PAC ACAIACA 2026 - INSTALADOR"
echo "   Sistema de Planejamento Anual de Contratações"
echo "=============================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}Por favor, execute como root (sudo)${NC}"
  exit 1
fi

echo -e "${GREEN}✓${NC} Verificando pré-requisitos..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker não encontrado. Instalando...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose não encontrado. Instalando...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}✓${NC} Docker e Docker Compose instalados"

# Perguntar informações
echo ""
echo "Configuração do Sistema:"
echo ""

read -p "Digite o domínio (ex: pac.acaiaca.mg.gov.br): " DOMAIN
read -p "Digite um email para notificações: " ADMIN_EMAIL

# Gerar chave secreta JWT
JWT_SECRET=$(openssl rand -base64 32)

echo ""
echo -e "${GREEN}✓${NC} Configuração coletada"

# Criar diretórios
mkdir -p /opt/pac-acaiaca
cd /opt/pac-acaiaca

# Criar arquivo .env
cat > .env <<EOL
# PAC Acaiaca 2026 - Configurações de Produção
DOMAIN=${DOMAIN}
ADMIN_EMAIL=${ADMIN_EMAIL}
JWT_SECRET=${JWT_SECRET}
MONGO_URL=mongodb://mongodb:27017
DB_NAME=pac_acaiaca
CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN}
REACT_APP_BACKEND_URL=https://${DOMAIN}
EOL

echo -e "${GREEN}✓${NC} Arquivo .env criado"

# Baixar arquivos do repositório
echo ""
echo -e "${YELLOW}Baixando arquivos do sistema...${NC}"

# Aqui você colocaria o comando para baixar os arquivos
# git clone [SEU_REPOSITORIO] .

# Criar arquivo docker-compose.yml local
cat > docker-compose.yml <<'EOL'
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: pac_mongodb
    restart: always
    environment:
      MONGO_INITDB_DATABASE: ${DB_NAME}
    volumes:
      - mongodb_data:/data/db
    networks:
      - pac_network

  backend:
    build: ./backend
    container_name: pac_backend
    restart: always
    depends_on:
      - mongodb
    env_file:
      - .env
    ports:
      - "8001:8001"
    networks:
      - pac_network

  frontend:
    build: ./frontend
    container_name: pac_frontend
    restart: always
    depends_on:
      - backend
    env_file:
      - .env
    networks:
      - pac_network

  nginx:
    image: nginx:alpine
    container_name: pac_nginx
    restart: always
    depends_on:
      - frontend
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    networks:
      - pac_network

volumes:
  mongodb_data:

networks:
  pac_network:
    driver: bridge
EOL

# Configurar Nginx
mkdir -p nginx
cat > nginx/nginx.conf <<EOL
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name ${DOMAIN};

        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_cache_bypass \$http_upgrade;
        }

        location /api {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host \$host;
            proxy_cache_bypass \$http_upgrade;
        }
    }
}
EOL

echo -e "${GREEN}✓${NC} Configuração Nginx criada"

# Instalar certificado SSL com Certbot
echo ""
echo -e "${YELLOW}Instalando certificado SSL...${NC}"
if command -v certbot &> /dev/null; then
    certbot certonly --standalone -d ${DOMAIN} --email ${ADMIN_EMAIL} --agree-tos --non-interactive || echo -e "${YELLOW}Aviso: Não foi possível instalar SSL automaticamente${NC}"
else
    echo -e "${YELLOW}Certbot não instalado. Instale manualmente para HTTPS${NC}"
fi

# Build e start dos containers
echo ""
echo -e "${YELLOW}Iniciando containers...${NC}"
docker-compose up -d --build

echo ""
echo "=============================================="
echo -e "${GREEN}✓ INSTALAÇÃO CONCLUÍDA!${NC}"
echo "=============================================="
echo ""
echo "Informações de Acesso:"
echo ""
echo "  URL: http://${DOMAIN}"
echo "  Usuário Admin: cristiano.abdo@acaiaca.mg.gov.br"
echo "  Senha: Cris@820906"
echo ""
echo "⚠️  IMPORTANTE: Altere a senha após o primeiro login!"
echo ""
echo "Status dos serviços:"
docker-compose ps
echo ""
echo "Para ver logs: docker-compose logs -f"
echo "Para parar: docker-compose down"
echo "Para reiniciar: docker-compose restart"
echo ""
echo "=============================================="
echo "Desenvolvido por Cristiano Abdo de Souza"
echo "Assessor de Planejamento, Compras e Logística"
echo "=============================================="
