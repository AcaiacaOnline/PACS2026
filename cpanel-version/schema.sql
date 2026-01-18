-- ============================================
-- Planejamento Acaiaca - Esquema MySQL para cPanel
-- Sistema de Gestão Municipal
-- ============================================

-- Configurações de charset
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================
-- TABELA DE USUÁRIOS
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    tipo_usuario ENUM('SERVIDOR', 'PESSOA_EXTERNA') DEFAULT 'SERVIDOR',
    picture TEXT,
    -- Permissões JSON
    permissions JSON,
    -- Dados de assinatura
    cpf VARCHAR(14),
    cargo VARCHAR(255),
    endereco TEXT,
    cep VARCHAR(10),
    telefone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- SESSÕES DE USUÁRIO
-- ============================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    session_token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_token (session_token(255)),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PAC INDIVIDUAL
-- ============================================
CREATE TABLE IF NOT EXISTS pacs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pac_id VARCHAR(50) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    secretaria VARCHAR(255) NOT NULL,
    secretario VARCHAR(255) NOT NULL,
    fiscal VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(255),
    endereco TEXT,
    ano VARCHAR(4) DEFAULT '2026',
    codigo_classificacao VARCHAR(20),
    subitem_classificacao VARCHAR(255),
    total_value DECIMAL(15,2) DEFAULT 0.00,
    stats JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_pac_id (pac_id),
    INDEX idx_ano (ano),
    INDEX idx_secretaria (secretaria(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pac_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id VARCHAR(50) NOT NULL UNIQUE,
    pac_id VARCHAR(50) NOT NULL,
    tipo VARCHAR(100),
    catmat VARCHAR(50),
    descricao TEXT NOT NULL,
    unidade VARCHAR(20),
    quantidade DECIMAL(15,4) DEFAULT 0,
    valor_unitario DECIMAL(15,2) DEFAULT 0.00,
    valor_total DECIMAL(15,2) DEFAULT 0.00,
    prioridade VARCHAR(50),
    justificativa TEXT,
    codigo_classificacao VARCHAR(20),
    subitem_classificacao VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item_id (item_id),
    INDEX idx_pac_id (pac_id),
    FOREIGN KEY (pac_id) REFERENCES pacs(pac_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PAC GERAL
-- ============================================
CREATE TABLE IF NOT EXISTS pacs_geral (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pac_geral_id VARCHAR(50) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    nome_secretaria VARCHAR(255) NOT NULL,
    secretario VARCHAR(255) NOT NULL,
    fiscal_contrato VARCHAR(255),
    telefone VARCHAR(20),
    email VARCHAR(255),
    endereco TEXT,
    cep VARCHAR(10),
    ano VARCHAR(4) DEFAULT '2026',
    secretarias_selecionadas JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_pac_geral_id (pac_geral_id),
    INDEX idx_ano (ano)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pac_geral_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id VARCHAR(50) NOT NULL UNIQUE,
    pac_geral_id VARCHAR(50) NOT NULL,
    catmat VARCHAR(50),
    descricao TEXT NOT NULL,
    unidade VARCHAR(20),
    qtd_ad DECIMAL(15,4) DEFAULT 0,
    qtd_fa DECIMAL(15,4) DEFAULT 0,
    qtd_sa DECIMAL(15,4) DEFAULT 0,
    qtd_se DECIMAL(15,4) DEFAULT 0,
    qtd_as DECIMAL(15,4) DEFAULT 0,
    qtd_ag DECIMAL(15,4) DEFAULT 0,
    qtd_ob DECIMAL(15,4) DEFAULT 0,
    qtd_tr DECIMAL(15,4) DEFAULT 0,
    qtd_cul DECIMAL(15,4) DEFAULT 0,
    quantidade_total DECIMAL(15,4) DEFAULT 0,
    valor_unitario DECIMAL(15,2) DEFAULT 0.00,
    valor_total DECIMAL(15,2) DEFAULT 0.00,
    prioridade VARCHAR(50),
    justificativa TEXT,
    codigo_classificacao VARCHAR(20),
    subitem_classificacao VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item_id (item_id),
    INDEX idx_pac_geral_id (pac_geral_id),
    FOREIGN KEY (pac_geral_id) REFERENCES pacs_geral(pac_geral_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PAC OBRAS
-- ============================================
CREATE TABLE IF NOT EXISTS pacs_geral_obras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pac_obras_id VARCHAR(50) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    nome_secretaria VARCHAR(255) NOT NULL,
    secretario VARCHAR(255) NOT NULL,
    fiscal_contrato VARCHAR(255),
    telefone VARCHAR(20),
    email VARCHAR(255),
    endereco TEXT,
    cep VARCHAR(10),
    ano VARCHAR(4) DEFAULT '2026',
    tipo_contratacao ENUM('OBRAS', 'SERVICOS') DEFAULT 'OBRAS',
    secretarias_selecionadas JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_pac_obras_id (pac_obras_id),
    INDEX idx_ano (ano)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pac_obras_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id VARCHAR(50) NOT NULL UNIQUE,
    pac_obras_id VARCHAR(50) NOT NULL,
    catmat VARCHAR(50),
    descricao TEXT NOT NULL,
    unidade VARCHAR(20),
    qtd_ad DECIMAL(15,4) DEFAULT 0,
    qtd_fa DECIMAL(15,4) DEFAULT 0,
    qtd_sa DECIMAL(15,4) DEFAULT 0,
    qtd_se DECIMAL(15,4) DEFAULT 0,
    qtd_as DECIMAL(15,4) DEFAULT 0,
    qtd_ag DECIMAL(15,4) DEFAULT 0,
    qtd_ob DECIMAL(15,4) DEFAULT 0,
    qtd_tr DECIMAL(15,4) DEFAULT 0,
    qtd_cul DECIMAL(15,4) DEFAULT 0,
    quantidade_total DECIMAL(15,4) DEFAULT 0,
    valor_unitario DECIMAL(15,2) DEFAULT 0.00,
    valor_total DECIMAL(15,2) DEFAULT 0.00,
    prioridade VARCHAR(50),
    justificativa TEXT,
    codigo_classificacao VARCHAR(20),
    subitem_classificacao VARCHAR(255),
    prazo_execucao INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item_id (item_id),
    INDEX idx_pac_obras_id (pac_obras_id),
    FOREIGN KEY (pac_obras_id) REFERENCES pacs_geral_obras(pac_obras_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- PROCESSOS
-- ============================================
CREATE TABLE IF NOT EXISTS processos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    processo_id VARCHAR(50) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    numero_processo VARCHAR(50) NOT NULL,
    modalidade_contratacao VARCHAR(100),
    status VARCHAR(100),
    objeto TEXT,
    responsavel VARCHAR(255),
    data_inicio DATE,
    data_autuacao DATE,
    data_contrato DATE,
    secretaria VARCHAR(255),
    secretario VARCHAR(255),
    ano INT DEFAULT 2025,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_processo_id (processo_id),
    INDEX idx_numero_processo (numero_processo),
    INDEX idx_ano (ano),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- DOEM (Diário Oficial Eletrônico Municipal)
-- ============================================
CREATE TABLE IF NOT EXISTS doem_edicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    edicao_id VARCHAR(50) NOT NULL UNIQUE,
    numero_edicao INT NOT NULL,
    ano INT NOT NULL,
    data_publicacao DATE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('rascunho', 'agendado', 'publicado') DEFAULT 'rascunho',
    publicacoes JSON,
    criado_por VARCHAR(50),
    assinatura_digital JSON,
    notificacao_enviada BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_edicao_id (edicao_id),
    INDEX idx_numero_edicao (numero_edicao),
    INDEX idx_ano (ano),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS doem_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_id VARCHAR(50) DEFAULT 'doem_config_main',
    nome_municipio VARCHAR(255) DEFAULT 'Acaiaca',
    uf VARCHAR(2) DEFAULT 'MG',
    prefeito VARCHAR(255),
    ano_inicio INT DEFAULT 2026,
    ultimo_numero_edicao INT DEFAULT 0,
    segmentos JSON,
    tipos_publicacao JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- NEWSLETTER
-- ============================================
CREATE TABLE IF NOT EXISTS doem_newsletter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inscrito_id VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    tipo ENUM('publico', 'usuario', 'manual') DEFAULT 'publico',
    ativo BOOLEAN DEFAULT TRUE,
    segmentos_interesse JSON,
    data_inscricao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP,
    confirmado BOOLEAN DEFAULT FALSE,
    token_confirmacao VARCHAR(255),
    INDEX idx_inscrito_id (inscrito_id),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- MROSC (Prestação de Contas)
-- ============================================
CREATE TABLE IF NOT EXISTS mrosc_projetos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projeto_id VARCHAR(50) NOT NULL UNIQUE,
    user_id VARCHAR(50) NOT NULL,
    nome_projeto VARCHAR(255) NOT NULL,
    objeto TEXT,
    organizacao_parceira VARCHAR(255),
    cnpj_parceira VARCHAR(20),
    responsavel_osc VARCHAR(255),
    data_inicio DATE,
    data_conclusao DATE,
    prazo_meses INT,
    valor_total DECIMAL(15,2) DEFAULT 0.00,
    valor_repasse_publico DECIMAL(15,2) DEFAULT 0.00,
    valor_contrapartida DECIMAL(15,2) DEFAULT 0.00,
    status ENUM('ELABORACAO', 'SUBMETIDO', 'ANALISE', 'CORRECAO', 'APROVADO', 'EXECUCAO', 'CONCLUIDO') DEFAULT 'ELABORACAO',
    -- Workflow fields
    data_submissao TIMESTAMP NULL,
    data_recebimento TIMESTAMP NULL,
    recebido_por VARCHAR(50),
    data_aprovacao TIMESTAMP NULL,
    aprovado_por VARCHAR(50),
    observacao_correcao TEXT,
    observacao_aprovacao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_projeto_id (projeto_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mrosc_rh (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rh_id VARCHAR(50) NOT NULL UNIQUE,
    projeto_id VARCHAR(50) NOT NULL,
    nome_funcao VARCHAR(255) NOT NULL,
    regime_contratacao VARCHAR(50),
    carga_horaria_semanal INT,
    salario_bruto DECIMAL(15,2) DEFAULT 0.00,
    provisao_ferias DECIMAL(15,2) DEFAULT 0.00,
    provisao_13_salario DECIMAL(15,2) DEFAULT 0.00,
    fgts DECIMAL(15,2) DEFAULT 0.00,
    inss_patronal DECIMAL(15,2) DEFAULT 0.00,
    vale_transporte DECIMAL(15,2) DEFAULT 0.00,
    vale_alimentacao DECIMAL(15,2) DEFAULT 0.00,
    custo_mensal_total DECIMAL(15,2) DEFAULT 0.00,
    numero_meses INT,
    custo_total_projeto DECIMAL(15,2) DEFAULT 0.00,
    orcamento_1 DECIMAL(15,2),
    orcamento_2 DECIMAL(15,2),
    orcamento_3 DECIMAL(15,2),
    media_orcamentos DECIMAL(15,2),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rh_id (rh_id),
    INDEX idx_projeto_id (projeto_id),
    FOREIGN KEY (projeto_id) REFERENCES mrosc_projetos(projeto_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mrosc_despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    despesa_id VARCHAR(50) NOT NULL UNIQUE,
    projeto_id VARCHAR(50) NOT NULL,
    natureza_despesa VARCHAR(20),
    item_despesa VARCHAR(255),
    descricao TEXT,
    unidade VARCHAR(20),
    quantidade DECIMAL(15,4) DEFAULT 0,
    orcamento_1 DECIMAL(15,2),
    orcamento_2 DECIMAL(15,2),
    orcamento_3 DECIMAL(15,2),
    media_orcamentos DECIMAL(15,2),
    valor_unitario DECIMAL(15,2) DEFAULT 0.00,
    valor_total DECIMAL(15,2) DEFAULT 0.00,
    referencia_preco_municipal DECIMAL(15,2),
    observacoes TEXT,
    justificativa TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_despesa_id (despesa_id),
    INDEX idx_projeto_id (projeto_id),
    FOREIGN KEY (projeto_id) REFERENCES mrosc_projetos(projeto_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mrosc_documentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    documento_id VARCHAR(50) NOT NULL UNIQUE,
    projeto_id VARCHAR(50) NOT NULL,
    despesa_id VARCHAR(50),
    tipo_documento VARCHAR(50),
    numero_documento VARCHAR(100),
    data_documento DATE,
    valor DECIMAL(15,2) DEFAULT 0.00,
    arquivo_url VARCHAR(500),
    arquivo_nome VARCHAR(255),
    arquivo_tamanho INT,
    validado BOOLEAN DEFAULT FALSE,
    validado_por VARCHAR(50),
    data_validacao TIMESTAMP NULL,
    observacoes_validacao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_documento_id (documento_id),
    INDEX idx_projeto_id (projeto_id),
    FOREIGN KEY (projeto_id) REFERENCES mrosc_projetos(projeto_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS mrosc_historico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    historico_id VARCHAR(50) NOT NULL UNIQUE,
    projeto_id VARCHAR(50) NOT NULL,
    acao VARCHAR(100) NOT NULL,
    usuario_id VARCHAR(50),
    usuario_nome VARCHAR(255),
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observacao TEXT,
    INDEX idx_historico_id (historico_id),
    INDEX idx_projeto_id (projeto_id),
    FOREIGN KEY (projeto_id) REFERENCES mrosc_projetos(projeto_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- ASSINATURAS DIGITAIS
-- ============================================
CREATE TABLE IF NOT EXISTS document_signatures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    signature_id VARCHAR(50) NOT NULL UNIQUE,
    validation_code VARCHAR(50) NOT NULL UNIQUE,
    document_type VARCHAR(100),
    hash_document VARCHAR(500),
    signers JSON,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_signature_id (signature_id),
    INDEX idx_validation_code (validation_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- INSERIR USUÁRIO ADMINISTRADOR PADRÃO
-- ============================================
INSERT INTO users (user_id, email, name, password_hash, is_admin, is_active, tipo_usuario)
VALUES (
    'user_admin_001',
    'admin@acaiaca.mg.gov.br',
    'Administrador',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJzFhgAe', -- senha: Admin@123
    TRUE,
    TRUE,
    'SERVIDOR'
) ON DUPLICATE KEY UPDATE name = name;

-- ============================================
-- INSERIR CONFIGURAÇÃO INICIAL DO DOEM
-- ============================================
INSERT INTO doem_config (config_id, nome_municipio, uf, ano_inicio, ultimo_numero_edicao)
VALUES ('doem_config_main', 'Acaiaca', 'MG', 2026, 0)
ON DUPLICATE KEY UPDATE nome_municipio = nome_municipio;
