# 🚀 PAC Acaiaca 2026 - Instalação em cPanel

**Versão PHP + MySQL para Hospedagem Tradicional**

Desenvolvido por **Cristiano Abdo de Souza**  
Assessor de Planejamento, Compras e Logística  
Prefeitura Municipal de Acaiaca - MG

---

## 📦 GUIA DE INSTALAÇÃO RÁPIDA

### Passo 1: Fazer Upload dos Arquivos

1. **Acesse o cPanel da sua hospedagem**
2. **Abra o Gerenciador de Arquivos**
3. **Navegue até `public_html` (ou pasta do domínio)**
4. **Faça upload do arquivo `pac-acaiaca-cpanel.zip`**
5. **Extraia o arquivo ZIP**

### Passo 2: Criar Banco de Dados

1. **No cPanel, abra "MySQL Databases"**
2. **Crie um novo banco:**
   - Nome: `pac_acaiaca` (ou outro de sua escolha)
3. **Crie um usuário do banco:**
   - Usuário: escolha um nome
   - Senha: gere uma senha forte
4. **Adicione o usuário ao banco** com TODOS os privilégios

### Passo 3: Executar o Instalador Web

1. **Acesse:** `https://pac.acaiaca.mg.gov.br/install/`
2. **Siga o assistente de instalação:**
   - Passo 1: Bem-vindo (clique em "Iniciar")
   - Passo 2: Configure o banco de dados
     - Host: `localhost`
     - Nome do Banco: `pac_acaiaca` (ou o que você criou)
     - Usuário: o usuário que você criou
     - Senha: a senha do usuário
     - URL: `https://pac.acaiaca.mg.gov.br`
   - Passo 3: Instalação concluída!

### Passo 4: Remover Instalador (Segurança)

1. **Via Gerenciador de Arquivos:**
   - Exclua ou renomeie a pasta `/install/`
2. **Via FTP/SSH:**
   ```bash
   rm -rf /caminho/para/public_html/install/
   ```

### Passo 5: Acessar o Sistema

1. **URL:** `https://pac.acaiaca.mg.gov.br`
2. **Email:** `cristiano.abdo@acaiaca.mg.gov.br`
3. **Senha:** `Cris@820906`

⚠️ **IMPORTANTE:** Altere a senha imediatamente!

---

## 📋 REQUISITOS TÉCNICOS

### Obrigatórios
- ✅ PHP 7.4 ou superior (recomendado 8.0+)
- ✅ MySQL 5.7 ou superior (ou MariaDB 10.2+)
- ✅ Extensões PHP:
  - PDO
  - PDO_MySQL
  - mbstring
  - json
  - openssl
- ✅ Permissões de escrita no diretório

### Recomendados
- ✅ SSL/HTTPS configurado
- ✅ mod_rewrite habilitado (Apache)
- ✅ PHP memory_limit: 128MB+
- ✅ PHP max_execution_time: 60s+

---

## 🔧 CONFIGURAÇÃO MANUAL (Avançado)

### Se o instalador web não funcionar:

#### 1. Criar config.php manualmente

Renomeie `config.sample.php` para `config.php` e edite:

```php
<?php
define('DB_HOST', 'localhost');
define('DB_NAME', 'pac_acaiaca');
define('DB_USER', 'seu_usuario_mysql');
define('DB_PASS', 'sua_senha_mysql');
define('DB_CHARSET', 'utf8mb4');
define('JWT_SECRET', 'GERE_UMA_CHAVE_ALEATORIA_AQUI');
define('JWT_EXPIRATION', 7 * 24 * 60 * 60);
define('BASE_URL', 'https://pac.acaiaca.mg.gov.br');
date_default_timezone_set('America/Sao_Paulo');
?>
```

**Gerar chave JWT segura:**
```bash
php -r "echo bin2hex(random_bytes(32));"
```

#### 2. Importar banco de dados

Via phpMyAdmin ou linha de comando:

```bash
mysql -u seu_usuario -p pac_acaiaca < install/schema.sql
```

#### 3. Criar usuário admin

Execute no MySQL/phpMyAdmin:

```sql
INSERT INTO users (user_id, email, name, password_hash, is_admin, is_active, created_at) 
VALUES (
  'user_admin001', 
  'cristiano.abdo@acaiaca.mg.gov.br', 
  'Cristiano Abdo de Souza',
  '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- senha: Cris@820906
  1, 
  1, 
  NOW()
);
```

---

## 🌐 CONFIGURAÇÃO DE DOMÍNIO

### Apontar Domínio para cPanel

1. **No Registro.br (ou seu registrador):**
   - Tipo: `A`
   - Nome: `pac` ou `@`
   - Destino: IP do servidor cPanel

2. **No cPanel:**
   - Acesse "Domínios" ou "Addon Domains"
   - Adicione: `pac.acaiaca.mg.gov.br`
   - Diretório: `public_html/pac` (ou raiz se for domínio principal)

### Configurar SSL (HTTPS)

**Opção 1: Let's Encrypt (via cPanel)**
1. Acesse "SSL/TLS Status"
2. Marque o domínio `pac.acaiaca.mg.gov.br`
3. Clique em "Run AutoSSL"

**Opção 2: Certificado Próprio**
1. Acesse "SSL/TLS"
2. Importe seu certificado

---

## ⚙️ CONFIGURAÇÕES DO .htaccess

O instalador cria automaticamente, mas se precisar:

```apache
# PAC Acaiaca 2026
RewriteEngine On
RewriteBase /

# Redirecionar para HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# API Routes
RewriteRule ^api/(.*)$ api/index.php [L]

# Frontend SPA
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.html [L]

# Security Headers
<IfModule mod_headers.c>
    Header set X-Content-Type-Options "nosniff"
    Header set X-Frame-Options "SAMEORIGIN"
    Header set X-XSS-Protection "1; mode=block"
    Header set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>

# Disable Directory Listing
Options -Indexes

# Protect config files
<FilesMatch "(config\.php|\.sql)">
    Order allow,deny
    Deny from all
</FilesMatch>
```

---

## 🐛 SOLUÇÃO DE PROBLEMAS

### Erro: "Não foi possível conectar ao banco"
- ✅ Verifique credenciais em `config.php`
- ✅ Confirme que o banco existe
- ✅ Verifique se o usuário tem permissões

### Erro: "Internal Server Error 500"
- ✅ Verifique logs de erro: cPanel > "Error Log"
- ✅ Aumente `memory_limit` no php.ini
- ✅ Verifique permissões de pasta (644 para arquivos, 755 para pastas)

### Página em branco após login
- ✅ Limpe cache do navegador
- ✅ Verifique se `mod_rewrite` está ativo
- ✅ Revise o `.htaccess`

### API não responde
- ✅ Teste: `https://seudominio.com/api/auth/me`
- ✅ Verifique se a pasta `/api/` existe
- ✅ Confirme permissões de execução PHP

---

## 📊 ESTRUTURA DE PASTAS

```
public_html/
├── api/                    # APIs REST
│   ├── index.php          # Router principal
│   ├── auth.php           # Autenticação
│   ├── pacs.php           # Gestão de PACs
│   └── users.php          # Gestão de usuários
├── assets/                 # CSS, JS, imagens
├── includes/              # Classes PHP
│   ├── Database.php       # Conexão BD
│   ├── Auth.php           # Autenticação
│   └── JWT.php            # Geração de tokens
├── install/               # Instalador (REMOVER após instalação)
│   ├── index.php
│   └── schema.sql
├── .htaccess              # Regras Apache
├── config.php             # Configurações (CRIAR)
├── config.sample.php      # Exemplo de config
├── index.html             # Frontend React (build)
└── README_INSTALACAO.md   # Este arquivo
```

---

## 🔒 SEGURANÇA

### Checklist Pós-Instalação

- [ ] ✅ Remover pasta `/install/`
- [ ] ✅ Alterar senha do admin
- [ ] ✅ Gerar nova chave JWT_SECRET
- [ ] ✅ Configurar SSL/HTTPS
- [ ] ✅ Desabilitar `display_errors` em produção
- [ ] ✅ Configurar backup automático
- [ ] ✅ Limitar tentativas de login
- [ ] ✅ Usar senhas fortes

### Backup Regular

**Via cPanel:**
1. Acesse "Backup"
2. Configure backup automático
3. Download manual: "Download a Full Website Backup"

**Via SSH:**
```bash
# Backup banco de dados
mysqldump -u usuario -p pac_acaiaca > backup_$(date +%Y%m%d).sql

# Backup arquivos
tar -czf backup_files_$(date +%Y%m%d).tar.gz /caminho/para/public_html/
```

---

## 📞 SUPORTE

**Desenvolvedor:** Cristiano Abdo de Souza  
**Email:** cristiano.abdo@acaiaca.mg.gov.br  
**Órgão:** Prefeitura Municipal de Acaiaca - MG

### Documentação Adicional
- Manual do Usuário: `/docs/manual_usuario.pdf`
- Vídeos tutoriais: Em desenvolvimento
- FAQ: `/docs/faq.md`

---

## 📜 CONFORMIDADE LEGAL

Sistema desenvolvido em conformidade com:
- ✅ Lei Federal nº 14.133/2021 (Nova Lei de Licitações)
- ✅ LGPD (Lei Geral de Proteção de Dados)
- ✅ Decreto Municipal de Acaiaca

---

## 🎓 PRÓXIMOS PASSOS

Após a instalação:

1. **Treinamento da Equipe**
   - Agendar sessão de capacitação
   - Distribuir manual do usuário
   - Definir administradores

2. **Configuração Inicial**
   - Criar usuários adicionais
   - Configurar permissões
   - Importar dados existentes (se houver)

3. **Testes**
   - Criar PAC de teste
   - Testar exportações (PDF/Excel)
   - Validar permissões de usuários

4. **Produção**
   - Anunciar sistema para secretarias
   - Estabelecer prazos
   - Monitorar uso inicial

---

**© 2026 Prefeitura Municipal de Acaiaca - MG**  
**Todos os direitos reservados**

---

## 🎉 INSTALAÇÃO SIMPLIFICADA - RESUMO

```bash
1. Upload dos arquivos para public_html/
2. Criar banco MySQL via cPanel
3. Acessar https://seudominio.com/install/
4. Seguir o assistente (3 passos)
5. Remover pasta /install/
6. Fazer login e trocar senha
7. Sistema pronto! ✅
```

**Tempo estimado:** 10-15 minutos

---

**Boa instalação!** 🚀
