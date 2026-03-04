# Guia de Instalação - Planejamento Acaiaca v3.0

## Índice
1. [Requisitos](#requisitos)
2. [Instalação em cPanel](#instalação-em-cpanel)
3. [Instalação em VPS](#instalação-em-vps)
4. [Configuração do MongoDB Atlas](#configuração-do-mongodb-atlas)
5. [Solução de Problemas](#solução-de-problemas)

---

## Requisitos

### Requisitos Mínimos
| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| RAM | 512MB | 1GB+ |
| Disco | 1GB | 2GB+ |
| Python | 3.8 | 3.10+ |
| CPU | 1 core | 2 cores |

### Software Necessário
- Python 3.8+ com pip e venv
- Acesso SSH ao servidor
- Banco de dados (MongoDB Atlas, MongoDB local ou SQLite)

---

## Instalação em cPanel

### Passo 1: Preparar MongoDB Atlas (Recomendado)

O cPanel compartilhado geralmente NÃO tem MongoDB instalado. Use MongoDB Atlas (gratuito):

1. Acesse [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Crie uma conta gratuita
3. Crie um cluster M0 (gratuito)
4. Em "Database Access", crie um usuário
5. Em "Network Access", adicione `0.0.0.0/0` (permite todos os IPs)
6. Em "Connect", copie a string de conexão

A string será algo como:
```
mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/planejamento_acaiaca
```

### Passo 2: Upload dos Arquivos

1. Acesse o cPanel via SSH ou Terminal
2. Faça upload do pacote `.zip` ou `.tar.gz`
3. Extraia:
```bash
# Para .zip
unzip planejamento-acaiaca-v3.0.0.zip

# Para .tar.gz
tar -xzf planejamento-acaiaca-v3.0.0.tar.gz
```

### Passo 3: Executar Instalador

```bash
cd planejamento-acaiaca-v3.0.0
chmod +x install.sh
./install.sh
```

Siga as instruções na tela:
1. Escolha o diretório de instalação
2. Selecione "MongoDB Atlas" como banco de dados
3. Cole a string de conexão do Atlas
4. Informe seu domínio

### Passo 4: Configurar Proxy no cPanel

Se o módulo `mod_proxy` estiver disponível, a configuração é automática.

Caso contrário, você precisará de um plano cPanel com:
- Application Manager
- Python App Selector

Ou configurar manualmente no `.htaccess`.

### Passo 5: Configurar SSL

1. No cPanel, vá em "SSL/TLS"
2. Instale um certificado Let's Encrypt (gratuito)
3. Ative "Force HTTPS"

---

## Instalação em VPS

### Ubuntu/Debian

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3 python3-pip python3-venv nginx certbot

# Instalar MongoDB (opcional, pode usar Atlas)
# wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
# echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
# sudo apt update
# sudo apt install -y mongodb-org

# Extrair e instalar
tar -xzf planejamento-acaiaca-v3.0.0.tar.gz
cd planejamento-acaiaca-v3.0.0
chmod +x install.sh
./install.sh
```

### Configurar Nginx

```bash
# Copiar configuração de exemplo
sudo cp nginx.conf.example /etc/nginx/sites-available/planejamento

# Editar com seu domínio
sudo nano /etc/nginx/sites-available/planejamento

# Ativar site
sudo ln -s /etc/nginx/sites-available/planejamento /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Configurar Systemd (Auto-start)

```bash
sudo nano /etc/systemd/system/planejamento.service
```

Conteúdo:
```ini
[Unit]
Description=Planejamento Acaiaca
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/planejamento-acaiaca/backend
Environment=PATH=/var/www/planejamento-acaiaca/backend/venv/bin
ExecStart=/var/www/planejamento-acaiaca/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable planejamento
sudo systemctl start planejamento
```

---

## Configuração do MongoDB Atlas

### Criar Cluster Gratuito

1. Faça login em [cloud.mongodb.com](https://cloud.mongodb.com)
2. Clique em "Build a Database"
3. Escolha "M0 FREE"
4. Selecione a região mais próxima (São Paulo se disponível)
5. Dê um nome ao cluster
6. Clique em "Create"

### Configurar Acesso

1. **Database Access** (menu lateral):
   - Clique em "Add New Database User"
   - Username: `planejamento_user`
   - Password: (gere uma senha forte)
   - Role: "Read and write to any database"
   - Clique em "Add User"

2. **Network Access** (menu lateral):
   - Clique em "Add IP Address"
   - Para cPanel compartilhado: `0.0.0.0/0` (permite todos)
   - Para VPS: adicione apenas o IP do servidor
   - Clique em "Confirm"

### Obter String de Conexão

1. Clique em "Connect" no cluster
2. Escolha "Connect your application"
3. Copie a string
4. Substitua `<password>` pela senha criada
5. Adicione o nome do banco: `/planejamento_acaiaca`

Exemplo final:
```
mongodb+srv://planejamento_user:SuaSenhaAqui@cluster0.abc123.mongodb.net/planejamento_acaiaca?retryWrites=true&w=majority
```

---

## Solução de Problemas

### Erro: "Python 3.8+ necessário"
```bash
# Ubuntu/Debian
sudo apt install python3.10 python3.10-venv

# CentOS/RHEL
sudo yum install python310
```

### Erro: "pip not found"
```bash
python3 -m ensurepip --upgrade
# ou
curl https://bootstrap.pypa.io/get-pip.py | python3
```

### Erro: "mod_proxy not available" (cPanel)
- Solicite ao suporte da hospedagem para ativar o módulo
- Ou use um plano VPS/dedicado

### Erro: "Connection refused" na API
1. Verifique se a aplicação está rodando:
```bash
./manage.sh status
```
2. Verifique os logs:
```bash
./manage.sh logs
```
3. Verifique se a porta não está bloqueada:
```bash
curl http://localhost:8001/api/health
```

### Erro: "MongoDB connection failed"
1. Verifique a string de conexão
2. Confirme que o IP está liberado no Atlas
3. Teste a conexão:
```bash
python3 -c "from pymongo import MongoClient; c = MongoClient('SUA_STRING'); print(c.server_info())"
```

### Frontend não carrega
1. Verifique se os arquivos estão em `public_html`
2. Verifique o `.htaccess`
3. Limpe o cache do navegador (Ctrl+Shift+R)

### PWA não instala
1. O site DEVE estar em HTTPS
2. Verifique se o `manifest.json` está acessível
3. Verifique os ícones em `/icons/`

---

## Contato e Suporte

- **Documentação**: Este arquivo
- **Logs**: `logs/app.log`
- **Email**: suporte@acaiaca.mg.gov.br
