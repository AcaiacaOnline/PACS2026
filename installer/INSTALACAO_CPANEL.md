# 🚀 PAC Acaiaca 2026 - Guia de Instalação para cPanel

**Desenvolvido por Cristiano Abdo de Souza**  
*Assessor de Planejamento, Compras e Logística*  
*Prefeitura Municipal de Acaiaca - MG*

---

## ⚠️ AVISO IMPORTANTE

Este sistema foi desenvolvido com tecnologias modernas:
- **Backend:** Python/FastAPI
- **Frontend:** React
- **Banco de Dados:** MongoDB

**Hospedagens tradicionais de cPanel geralmente usam PHP + MySQL**, o que não é compatível diretamente com esta aplicação.

---

## ✅ OPÇÕES DE HOSPEDAGEM RECOMENDADAS

### Opção 1: Emergent (Recomendado - Mais Fácil)

A plataforma onde o sistema foi desenvolvido oferece deploy com 1 clique:

1. Acesse: https://app.emergent.sh
2. Faça login ou crie uma conta
3. Importe este projeto
4. Configure o domínio: pac.acaiaca.mg.gov.br
5. Deploy automático!

**Vantagens:**
- ✅ Sem configuração manual
- ✅ SSL automático
- ✅ Atualizações fáceis
- ✅ Suporte técnico incluído
- ✅ Backup automático

### Opção 2: VPS/Cloud (Para Administradores de Sistema)

Provedores recomendados:
- **DigitalOcean** (mais popular)
- **AWS** (Amazon Web Services)
- **Google Cloud**
- **Azure** (Microsoft)
- **Contabo** (custo-benefício)

**Requisitos mínimos:**
- 2GB RAM
- 2 CPU cores
- 20GB SSD
- Ubuntu 20.04+ ou CentOS 8+

### Opção 3: Hospedagem Especializada em Node.js/Python

Provedores que suportam a stack do sistema:
- Heroku
- Railway.app
- Render.com
- Vercel (frontend) + MongoDB Atlas (banco)

---

## 📦 INSTALAÇÃO EM VPS (Ubuntu)

### 1. Preparar o Servidor

```bash
# Conectar via SSH
ssh root@SEU_IP

# Atualizar sistema
apt update && apt upgrade -y

# Instalar dependências
apt install -y git curl wget nginx certbot python3-certbot-nginx
```

### 2. Instalar Docker e Docker Compose

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Instalar Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verificar instalação
docker --version
docker-compose --version
```

### 3. Baixar e Configurar o Sistema

```bash
# Criar diretório
mkdir -p /opt/pac-acaiaca
cd /opt/pac-acaiaca

# Baixar arquivos (substituir pela URL do seu repositório)
git clone https://github.com/seu-usuario/pac-acaiaca.git .

# OU fazer upload via SFTP/SCP dos arquivos

# Dar permissão ao script de instalação
chmod +x installer/install.sh

# Executar instalação automática
sudo ./installer/install.sh
```

### 4. Configurar DNS

No painel do seu domínio, adicione um registro A:

```
Tipo: A
Nome: pac (ou @)
Valor: IP_DO_SEU_SERVIDOR
TTL: 3600
```

Aguarde a propagação DNS (pode levar até 24h, mas geralmente é rápido).

### 5. Verificar Instalação

```bash
# Ver status dos containers
docker-compose ps

# Ver logs
docker-compose logs -f

# Acessar: http://pac.acaiaca.mg.gov.br
```

---

## 🔒 CONFIGURAR SSL (HTTPS)

### Método Automático com Certbot

```bash
# Instalar certbot
apt install certbot python3-certbot-nginx

# Obter certificado
certbot --nginx -d pac.acaiaca.mg.gov.br

# Renovação automática já está configurada!
```

---

## 👤 ACESSO INICIAL

Após a instalação, acesse:

```
URL: https://pac.acaiaca.mg.gov.br
Email: cristiano.abdo@acaiaca.mg.gov.br
Senha: Cris@820906
```

**⚠️ IMPORTANTE:** Altere a senha imediatamente após o primeiro login!

---

## 🔧 COMANDOS ÚTEIS

### Gerenciar Containers

```bash
# Iniciar
docker-compose up -d

# Parar
docker-compose down

# Reiniciar
docker-compose restart

# Ver logs
docker-compose logs -f [nome_do_servico]

# Atualizar sistema
git pull origin main
docker-compose up -d --build
```

### Backup do Banco de Dados

```bash
# Criar backup
docker exec pac_mongodb mongodump --out /data/backup

# Copiar backup para host
docker cp pac_mongodb:/data/backup ./backup_$(date +%Y%m%d)

# Restaurar backup
docker exec pac_mongodb mongorestore /data/backup
```

---

## ❌ INSTALAÇÃO EM CPANEL TRADICIONAL (NÃO RECOMENDADO)

Se você **realmente precisa** usar cPanel tradicional, será necessário:

1. **Adaptar o Backend para PHP:**
   - Reescrever toda a API em PHP
   - Migrar de MongoDB para MySQL
   - Adaptar autenticação JWT

2. **Adaptar o Frontend:**
   - Build estático do React
   - Upload para public_html
   - Configurar .htaccess

**Estimativa de trabalho:** 40-60 horas de desenvolvimento

**Não recomendamos** este caminho pois:
- ❌ Perde funcionalidades modernas
- ❌ Manutenção mais difícil
- ❌ Performance inferior
- ❌ Segurança comprometida

---

## 📞 SUPORTE TÉCNICO

**Desenvolvedor:** Cristiano Abdo de Souza  
**Email:** cristiano.abdo@acaiaca.mg.gov.br  
**Prefeitura Municipal de Acaiaca - MG**

Para questões técnicas complexas, considere contratar:
- Um desenvolvedor Python/React
- Um administrador de sistemas Linux
- Uma empresa de hospedagem gerenciada

---

## 📋 CHECKLIST PÓS-INSTALAÇÃO

- [ ] Sistema acessível via HTTPS
- [ ] SSL configurado e válido
- [ ] Login com usuário admin funcionando
- [ ] Senha do admin alterada
- [ ] Backup automático configurado
- [ ] Firewall configurado (portas 80, 443, 22)
- [ ] Monitoramento configurado
- [ ] DNS apontando corretamente
- [ ] Emails de notificação testados

---

## 🎓 TREINAMENTO DE USUÁRIOS

Após a instalação, recomendamos:

1. Sessão de treinamento para administradores
2. Manual do usuário disponibilizado
3. Vídeos tutoriais gravados
4. Suporte inicial de 30 dias

---

## 📜 CONFORMIDADE LEGAL

Este sistema foi desenvolvido em conformidade com:
- ✅ Lei Federal nº 14.133/2021 (Nova Lei de Licitações)
- ✅ LGPD (Lei Geral de Proteção de Dados)
- ✅ Princípios de Transparência Pública

---

**© 2026 Prefeitura Municipal de Acaiaca - MG**  
**Todos os direitos reservados**
