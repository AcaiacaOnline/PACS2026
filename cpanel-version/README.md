# Planejamento Acaiaca - Versão cPanel

Este diretório contém os arquivos necessários para instalar o Sistema de Gestão Municipal "Planejamento Acaiaca" em hospedagem compartilhada com cPanel.

## 📋 Requisitos

- PHP 7.4 ou superior
- MySQL 5.7+ ou MariaDB 10.3+
- Extensões PHP: PDO, PDO_MySQL, JSON, mbstring
- Acesso ao cPanel ou painel de controle equivalente

## 🚀 Instalação

### Passo 1: Criar Banco de Dados

1. Acesse o cPanel da sua hospedagem
2. Vá em "Bancos de Dados MySQL"
3. Crie um novo banco de dados (ex: `usuario_pacaiaca`)
4. Crie um novo usuário MySQL
5. Associe o usuário ao banco com TODOS os privilégios

### Passo 2: Upload dos Arquivos

1. Faça upload de todos os arquivos deste diretório para o `public_html` ou subdiretório desejado
2. Certifique-se de que os arquivos `.htaccess` foram enviados

### Passo 3: Executar Instalador

1. Acesse `https://seudominio.com.br/install.php` no navegador
2. Siga as instruções na tela:
   - Verificação de requisitos
   - Configuração do banco de dados
   - Configuração do sistema
3. Após a instalação, **remova ou renomeie o arquivo `install.php`**

### Passo 4: Primeiro Acesso

- **Email**: admin@acaiaca.mg.gov.br
- **Senha**: Admin@123

⚠️ **IMPORTANTE**: Altere a senha padrão imediatamente após o primeiro login!

## 📁 Estrutura de Arquivos

```
cpanel-version/
├── install.php      # Instalador interativo (remover após instalação)
├── schema.sql       # Estrutura do banco de dados MySQL
├── README.md        # Este arquivo
├── .htaccess        # Configurações do Apache
├── config/          # Diretório de configuração (criado pelo instalador)
├── uploads/         # Diretório de uploads (criado pelo instalador)
└── api/             # API PHP (a ser desenvolvida)
```

## 🔧 Configuração Manual

Se preferir instalar manualmente:

1. Importe o arquivo `schema.sql` no phpMyAdmin ou via linha de comando:
   ```bash
   mysql -u usuario -p nome_banco < schema.sql
   ```

2. Crie o arquivo `config/config.php` com as configurações:
   ```php
   <?php
   define('DB_HOST', 'localhost');
   define('DB_NAME', 'seu_banco');
   define('DB_USER', 'seu_usuario');
   define('DB_PASS', 'sua_senha');
   define('SITE_URL', 'https://seudominio.com.br');
   define('JWT_SECRET', 'sua_chave_secreta_32_caracteres');
   define('INSTALLED', true);
   ```

## 📞 Suporte

Em caso de dúvidas ou problemas:
- Verifique os logs de erro do PHP no cPanel
- Confirme que todas as extensões PHP estão habilitadas
- Verifique as permissões dos diretórios (755 para pastas, 644 para arquivos)

## ⚖️ Licença

Sistema desenvolvido para a Prefeitura Municipal de Acaiaca - MG.
Todos os direitos reservados.
