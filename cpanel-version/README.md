# Planejamento Acaiaca - Versão cPanel

## Requisitos do Servidor

### Requisitos Mínimos
- PHP 8.1 ou superior
- MySQL 8.0 ou MariaDB 10.5
- Apache com mod_rewrite
- 512MB de RAM mínimo
- 1GB de espaço em disco

### Extensões PHP Necessárias
- pdo_mysql
- mbstring
- json
- curl
- zip
- gd

## Instalação

### 1. Upload dos Arquivos
Faça upload de todos os arquivos para o diretório `public_html` via File Manager ou FTP.

### 2. Configurar Banco de Dados
1. Acesse **MySQL Databases** no cPanel
2. Crie um novo banco de dados: `seu_usuario_planejamento`
3. Crie um novo usuário de banco de dados
4. Adicione o usuário ao banco de dados com **ALL PRIVILEGES**

### 3. Configurar Variáveis de Ambiente
Renomeie o arquivo `.env.example` para `.env` e configure:

```env
DB_HOST=localhost
DB_NAME=seu_usuario_planejamento
DB_USER=seu_usuario_db
DB_PASSWORD=sua_senha_db
DB_PORT=3306

APP_URL=https://seu-dominio.com.br
APP_ENV=production
APP_DEBUG=false

JWT_SECRET=gere-uma-chave-aleatoria-aqui
```

### 4. Executar Instalação
Acesse no navegador: `https://seu-dominio.com.br/install.php`

### 5. Remover Instalador
Após a instalação, **REMOVA** o arquivo `install.php` por segurança.

## Estrutura de Arquivos

```
public_html/
├── api/
│   ├── index.php          # Roteador principal da API
│   ├── config.php         # Configurações
│   ├── database.php       # Conexão com banco
│   ├── auth.php           # Autenticação JWT
│   ├── routes/
│   │   ├── pacs.php
│   │   ├── processos.php
│   │   ├── mrosc.php
│   │   └── ...
│   └── models/
│       ├── User.php
│       ├── PAC.php
│       └── ...
├── frontend/
│   └── build/             # React build estático
├── uploads/               # Arquivos enviados
├── .htaccess              # Configuração Apache
├── .env                   # Variáveis de ambiente
└── install.php            # Instalador
```

## Conversão de MongoDB para MySQL

### Tabelas Principais

```sql
-- Usuários
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    tipo_usuario ENUM('servidor', 'externo') DEFAULT 'servidor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- PACs
CREATE TABLE pacs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pac_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    nome_secretaria VARCHAR(255),
    secretario VARCHAR(255),
    ano VARCHAR(4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ano (ano),
    INDEX idx_user (user_id)
);

-- Itens do PAC
CREATE TABLE pac_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id VARCHAR(50) UNIQUE NOT NULL,
    pac_id VARCHAR(50) NOT NULL,
    descricao TEXT,
    unidade VARCHAR(50),
    quantidade DECIMAL(15,4),
    valor_unitario DECIMAL(15,2),
    valor_total DECIMAL(15,2),
    codigo_classificacao VARCHAR(20),
    subitem_classificacao VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_pac (pac_id)
);

-- Processos
CREATE TABLE processos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    processo_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    numero_processo VARCHAR(100),
    modalidade_contratacao VARCHAR(100),
    status VARCHAR(100),
    objeto TEXT,
    responsavel VARCHAR(255),
    numero_modalidade VARCHAR(50),
    data_inicio DATE,
    data_autuacao DATE,
    data_contrato DATE,
    secretaria VARCHAR(255),
    secretario VARCHAR(255),
    observacoes TEXT,
    ano VARCHAR(4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ano (ano),
    INDEX idx_status (status)
);

-- Projetos MROSC
CREATE TABLE mrosc_projetos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    nome_projeto VARCHAR(255) NOT NULL,
    objeto TEXT,
    nome_osc VARCHAR(255),
    cnpj_osc VARCHAR(20),
    responsavel_osc VARCHAR(255),
    data_inicio DATE,
    data_fim DATE,
    prazo_meses INT,
    valor_total DECIMAL(15,2),
    valor_repasse_publico DECIMAL(15,2),
    valor_contrapartida DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'ELABORACAO',
    submetido BOOLEAN DEFAULT FALSE,
    aprovado BOOLEAN DEFAULT FALSE,
    pode_editar BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_user (user_id)
);

-- RH MROSC
CREATE TABLE mrosc_rh (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rh_id VARCHAR(50) UNIQUE NOT NULL,
    projeto_id VARCHAR(50) NOT NULL,
    nome_funcao VARCHAR(255),
    regime_contratacao VARCHAR(50),
    carga_horaria_semanal INT,
    salario_bruto DECIMAL(15,2),
    provisao_ferias DECIMAL(15,2),
    provisao_13_salario DECIMAL(15,2),
    fgts DECIMAL(15,2),
    inss_patronal DECIMAL(15,2),
    vale_transporte DECIMAL(15,2),
    vale_alimentacao DECIMAL(15,2),
    custo_mensal_total DECIMAL(15,2),
    numero_meses INT,
    custo_total_projeto DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_projeto (projeto_id)
);

-- Despesas MROSC
CREATE TABLE mrosc_despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    despesa_id VARCHAR(50) UNIQUE NOT NULL,
    projeto_id VARCHAR(50) NOT NULL,
    natureza_despesa VARCHAR(20),
    item_despesa VARCHAR(255),
    descricao TEXT,
    unidade VARCHAR(50),
    quantidade DECIMAL(15,4),
    orcamento_1 DECIMAL(15,2),
    orcamento_2 DECIMAL(15,2),
    orcamento_3 DECIMAL(15,2),
    media_orcamentos DECIMAL(15,2),
    valor_unitario DECIMAL(15,2),
    valor_total DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_projeto (projeto_id)
);

-- Documentos MROSC
CREATE TABLE mrosc_documentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    documento_id VARCHAR(50) UNIQUE NOT NULL,
    projeto_id VARCHAR(50) NOT NULL,
    despesa_id VARCHAR(50),
    tipo_documento VARCHAR(100),
    numero_documento VARCHAR(100),
    data_documento DATE,
    valor DECIMAL(15,2),
    arquivo_url VARCHAR(500),
    arquivo_nome VARCHAR(255),
    arquivo_tipo VARCHAR(100),
    arquivo_tamanho INT,
    validado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_projeto (projeto_id)
);
```

## Suporte

Em caso de problemas, entre em contato com o suporte técnico.
