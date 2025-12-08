# PAC Acaiaca 2026 - Instalador para cPanel

## 📦 Sistema de Planejamento Anual de Contratações
**Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística**

---

## 🚀 Instalação no cPanel

### Pré-requisitos
- Hospedagem cPanel com:
  - PHP 8.0 ou superior
  - MySQL 5.7 ou superior
  - Suporte a Python 3.9+ (opcional, para backend completo)
  - Node.js 16+ (opcional, para frontend React)

### Método 1: Instalação Rápida (Recomendado)

**Este sistema foi desenvolvido com FastAPI (Python) + React + MongoDB e requer um ambiente específico.**

Para instalação em servidores tradicionais com cPanel/MySQL, recomendamos:

1. **Utilizar a plataforma Emergent** (onde o sistema foi desenvolvido):
   - Acesse: https://app.emergent.sh
   - Faça deploy automático com 1 clique
   - Conecte seu domínio pac.acaiaca.mg.gov.br

2. **Alternativa: VPS/Cloud**:
   - DigitalOcean, AWS, Azure, Google Cloud
   - Deploy via Docker (arquivo docker-compose incluído)

### Método 2: Instalação Manual em Servidor Linux

#### 1. Clonar/Fazer Upload dos Arquivos

```bash
# Via SSH
cd /home/seuusuario/
git clone [URL_DO_REPOSITORIO] pac-acaiaca
cd pac-acaiaca
```

#### 2. Configurar Backend (Python/FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
nano .env
# Edite as variáveis:
# - MONGO_URL=mongodb://localhost:27017
# - DB_NAME=pac_acaiaca
# - JWT_SECRET=sua-chave-secreta-aqui
```

#### 3. Configurar Frontend (React)

```bash
cd frontend
yarn install

# Configurar .env
cp .env.example .env
nano .env
# Edite:
# - REACT_APP_BACKEND_URL=https://pac.acaiaca.mg.gov.br
```

#### 4. Build e Deploy

```bash
# Frontend
cd frontend
yarn build

# Copiar build para public_html
cp -r build/* /home/seuusuario/public_html/

# Backend (usar supervisor ou PM2)
cd backend
pm2 start "uvicorn server:app --host 0.0.0.0 --port 8001" --name pac-backend
```

#### 5. Configurar Nginx/Apache

**Nginx:**
```nginx
server {
    listen 80;
    server_name pac.acaiaca.mg.gov.br;
    
    location / {
        root /home/seuusuario/public_html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 🔧 Configuração de Produção

### Variáveis de Ambiente Essenciais

**Backend (.env):**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=pac_acaiaca
JWT_SECRET=GERE_UMA_CHAVE_FORTE_AQUI
CORS_ORIGINS=https://pac.acaiaca.mg.gov.br
```

**Frontend (.env):**
```
REACT_APP_BACKEND_URL=https://pac.acaiaca.mg.gov.br
```

### Criar Usuário Administrador Padrão

O sistema cria automaticamente no primeiro start:
- **Email:** cristiano.abdo@acaiaca.mg.gov.br
- **Senha:** Cris@820906

**⚠️ IMPORTANTE:** Altere a senha após o primeiro login!

---

## 📋 Funcionalidades

✅ Autenticação JWT + Google OAuth  
✅ Gerenciamento de Usuários (Admin/Padrão)  
✅ CRUD Completo de PACs  
✅ Gestão de Itens por PAC  
✅ Dashboard com Estatísticas  
✅ Exportação PDF Profissional  
✅ Exportação Excel Formatado  
✅ Importação em Lote (XLSX)  
✅ Controle de Permissões  
✅ Design Responsivo  

---

## 🆘 Suporte e Contato

**Desenvolvedor:** Cristiano Abdo de Souza  
**Cargo:** Assessor de Planejamento, Compras e Logística  
**Email:** cristiano.abdo@acaiaca.mg.gov.br  

---

## 📜 Licença

Sistema desenvolvido para a Prefeitura Municipal de Acaiaca-MG  
Em conformidade com a Lei Federal nº 14.133/2021  

© 2026 Prefeitura Municipal de Acaiaca - Todos os direitos reservados
