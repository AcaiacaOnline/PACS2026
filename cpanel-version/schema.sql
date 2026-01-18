-- Planejamento Acaiaca - Schema MySQL para cPanel
-- Versão: 2.0
-- Data: 2026

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Tabela de Usuários
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `user_id` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `name` VARCHAR(255) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `is_admin` TINYINT(1) DEFAULT 0,
    `is_active` TINYINT(1) DEFAULT 1,
    `tipo_usuario` ENUM('servidor', 'externo') DEFAULT 'servidor',
    `signature_data` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_email` (`email`),
    INDEX `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de PACs
-- ----------------------------
DROP TABLE IF EXISTS `pacs`;
CREATE TABLE `pacs` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `pac_id` VARCHAR(50) NOT NULL UNIQUE,
    `user_id` VARCHAR(50) NOT NULL,
    `nome_secretaria` VARCHAR(255),
    `secretario` VARCHAR(255),
    `email` VARCHAR(255),
    `fiscal_contrato` VARCHAR(255),
    `ano` VARCHAR(4) DEFAULT '2026',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_ano` (`ano`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_secretaria` (`nome_secretaria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Itens do PAC
-- ----------------------------
DROP TABLE IF EXISTS `pac_items`;
CREATE TABLE `pac_items` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `item_id` VARCHAR(50) NOT NULL UNIQUE,
    `pac_id` VARCHAR(50) NOT NULL,
    `descricao` TEXT,
    `unidade` VARCHAR(50),
    `quantidade_total` DECIMAL(15,4) DEFAULT 0,
    `valor_unitario` DECIMAL(15,2) DEFAULT 0,
    `valor_total` DECIMAL(15,2) DEFAULT 0,
    `codigo_classificacao` VARCHAR(20),
    `subitem_classificacao` VARCHAR(200),
    `quantidade_jan` DECIMAL(15,4) DEFAULT 0,
    `quantidade_fev` DECIMAL(15,4) DEFAULT 0,
    `quantidade_mar` DECIMAL(15,4) DEFAULT 0,
    `quantidade_abr` DECIMAL(15,4) DEFAULT 0,
    `quantidade_mai` DECIMAL(15,4) DEFAULT 0,
    `quantidade_jun` DECIMAL(15,4) DEFAULT 0,
    `quantidade_jul` DECIMAL(15,4) DEFAULT 0,
    `quantidade_ago` DECIMAL(15,4) DEFAULT 0,
    `quantidade_set` DECIMAL(15,4) DEFAULT 0,
    `quantidade_out` DECIMAL(15,4) DEFAULT 0,
    `quantidade_nov` DECIMAL(15,4) DEFAULT 0,
    `quantidade_dez` DECIMAL(15,4) DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_pac` (`pac_id`),
    INDEX `idx_classificacao` (`codigo_classificacao`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de PACs Geral
-- ----------------------------
DROP TABLE IF EXISTS `pacs_geral`;
CREATE TABLE `pacs_geral` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `pac_geral_id` VARCHAR(50) NOT NULL UNIQUE,
    `user_id` VARCHAR(50) NOT NULL,
    `nome_secretaria` VARCHAR(255),
    `secretario` VARCHAR(255),
    `email` VARCHAR(255),
    `fiscal_contrato` VARCHAR(255),
    `ano` VARCHAR(4) DEFAULT '2026',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_ano` (`ano`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Itens do PAC Geral
-- ----------------------------
DROP TABLE IF EXISTS `pac_geral_items`;
CREATE TABLE `pac_geral_items` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `item_id` VARCHAR(50) NOT NULL UNIQUE,
    `pac_geral_id` VARCHAR(50) NOT NULL,
    `descricao` TEXT,
    `unidade` VARCHAR(50),
    `quantidade_total` DECIMAL(15,4) DEFAULT 0,
    `valor_unitario` DECIMAL(15,2) DEFAULT 0,
    `valor_total` DECIMAL(15,2) DEFAULT 0,
    `codigo_classificacao` VARCHAR(20),
    `subitem_classificacao` VARCHAR(200),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_pac_geral` (`pac_geral_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de PACs Geral Obras
-- ----------------------------
DROP TABLE IF EXISTS `pacs_geral_obras`;
CREATE TABLE `pacs_geral_obras` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `pac_obras_id` VARCHAR(50) NOT NULL UNIQUE,
    `user_id` VARCHAR(50) NOT NULL,
    `nome_secretaria` VARCHAR(255),
    `secretario` VARCHAR(255),
    `email` VARCHAR(255),
    `fiscal_contrato` VARCHAR(255),
    `ano` VARCHAR(4) DEFAULT '2026',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_ano` (`ano`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Itens do PAC Geral Obras
-- ----------------------------
DROP TABLE IF EXISTS `pac_geral_obras_items`;
CREATE TABLE `pac_geral_obras_items` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `item_id` VARCHAR(50) NOT NULL UNIQUE,
    `pac_obras_id` VARCHAR(50) NOT NULL,
    `descricao` TEXT,
    `unidade` VARCHAR(50),
    `quantidade_total` DECIMAL(15,4) DEFAULT 0,
    `valor_unitario` DECIMAL(15,2) DEFAULT 0,
    `valor_total` DECIMAL(15,2) DEFAULT 0,
    `codigo_classificacao` VARCHAR(20),
    `subitem_classificacao` VARCHAR(200),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_pac_obras` (`pac_obras_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Processos
-- ----------------------------
DROP TABLE IF EXISTS `processos`;
CREATE TABLE `processos` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `processo_id` VARCHAR(50) NOT NULL UNIQUE,
    `user_id` VARCHAR(50) NOT NULL,
    `numero_processo` VARCHAR(100),
    `modalidade_contratacao` VARCHAR(100),
    `status` VARCHAR(100) DEFAULT 'Em Elaboração',
    `objeto` TEXT,
    `responsavel` VARCHAR(255),
    `numero_modalidade` VARCHAR(50),
    `data_inicio` DATE NULL,
    `data_autuacao` DATE NULL,
    `data_contrato` DATE NULL,
    `secretaria` VARCHAR(255),
    `secretario` VARCHAR(255),
    `observacoes` TEXT,
    `ano` VARCHAR(4) DEFAULT '2026',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_ano` (`ano`),
    INDEX `idx_status` (`status`),
    INDEX `idx_numero` (`numero_processo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Projetos MROSC
-- ----------------------------
DROP TABLE IF EXISTS `mrosc_projetos`;
CREATE TABLE `mrosc_projetos` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `projeto_id` VARCHAR(50) NOT NULL UNIQUE,
    `user_id` VARCHAR(50) NOT NULL,
    `nome_projeto` VARCHAR(255) NOT NULL,
    `objeto` TEXT,
    `nome_osc` VARCHAR(255),
    `cnpj_osc` VARCHAR(20),
    `responsavel_osc` VARCHAR(255),
    `email_osc` VARCHAR(255),
    `telefone_osc` VARCHAR(20),
    `endereco_osc` TEXT,
    `tipo_concedente` VARCHAR(100),
    `nome_concedente` VARCHAR(255),
    `numero_emenda` VARCHAR(100),
    `numero_termo` VARCHAR(100),
    `tipo_termo` VARCHAR(100),
    `numero_processo` VARCHAR(100),
    `banco` VARCHAR(100),
    `agencia` VARCHAR(20),
    `conta_bancaria` VARCHAR(30),
    `tipo_conta` VARCHAR(50),
    `gestor_responsavel` VARCHAR(255),
    `cpf_gestor` VARCHAR(14),
    `cargo_gestor` VARCHAR(100),
    `data_inicio` DATE,
    `data_fim` DATE,
    `prazo_meses` INT DEFAULT 12,
    `valor_total` DECIMAL(15,2) DEFAULT 0,
    `valor_repasse_publico` DECIMAL(15,2) DEFAULT 0,
    `valor_contrapartida` DECIMAL(15,2) DEFAULT 0,
    `objeto_detalhado` TEXT,
    `justificativa` TEXT,
    `publico_alvo` VARCHAR(255),
    `quantidade_beneficiarios` INT,
    `metodologia` TEXT,
    `resultados_esperados` TEXT,
    `status` VARCHAR(50) DEFAULT 'ELABORACAO',
    `submetido` TINYINT(1) DEFAULT 0,
    `data_submissao` DATETIME NULL,
    `submetido_por` VARCHAR(50),
    `recebido` TINYINT(1) DEFAULT 0,
    `data_recebimento` DATETIME NULL,
    `recebido_por` VARCHAR(50),
    `pode_editar` TINYINT(1) DEFAULT 1,
    `aprovado` TINYINT(1) DEFAULT 0,
    `data_aprovacao` DATETIME NULL,
    `aprovado_por` VARCHAR(50),
    `observacoes_aprovacao` TEXT,
    `correcao_solicitada` TINYINT(1) DEFAULT 0,
    `data_correcao_solicitada` DATETIME NULL,
    `motivo_correcao` TEXT,
    `solicitado_por` VARCHAR(50),
    `historico_status` JSON,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_status` (`status`),
    INDEX `idx_user` (`user_id`),
    INDEX `idx_osc` (`cnpj_osc`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de RH MROSC
-- ----------------------------
DROP TABLE IF EXISTS `mrosc_rh`;
CREATE TABLE `mrosc_rh` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `rh_id` VARCHAR(50) NOT NULL UNIQUE,
    `projeto_id` VARCHAR(50) NOT NULL,
    `nome_funcao` VARCHAR(255),
    `codigo_cbo` VARCHAR(20),
    `regime_contratacao` VARCHAR(50),
    `tipo_vinculo` VARCHAR(50),
    `carga_horaria_semanal` INT,
    `carga_horaria_mensal` INT,
    `salario_bruto` DECIMAL(15,2) DEFAULT 0,
    `provisao_ferias` DECIMAL(15,2) DEFAULT 0,
    `provisao_13_salario` DECIMAL(15,2) DEFAULT 0,
    `fgts` DECIMAL(15,2) DEFAULT 0,
    `fgts_rescisao` DECIMAL(15,2) DEFAULT 0,
    `inss_patronal` DECIMAL(15,2) DEFAULT 0,
    `outros_encargos` DECIMAL(15,2) DEFAULT 0,
    `vale_transporte` DECIMAL(15,2) DEFAULT 0,
    `vale_alimentacao` DECIMAL(15,2) DEFAULT 0,
    `plano_saude` DECIMAL(15,2) DEFAULT 0,
    `outros_beneficios` DECIMAL(15,2) DEFAULT 0,
    `custo_mensal_encargos` DECIMAL(15,2) DEFAULT 0,
    `custo_mensal_beneficios` DECIMAL(15,2) DEFAULT 0,
    `custo_mensal_total` DECIMAL(15,2) DEFAULT 0,
    `numero_meses` INT DEFAULT 12,
    `custo_total_projeto` DECIMAL(15,2) DEFAULT 0,
    `orcamento_1` DECIMAL(15,2),
    `orcamento_2` DECIMAL(15,2),
    `orcamento_3` DECIMAL(15,2),
    `media_orcamentos` DECIMAL(15,2),
    `valor_referencia_municipal` DECIMAL(15,2),
    `observacoes` TEXT,
    `justificativa_valor` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_projeto` (`projeto_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Despesas MROSC
-- ----------------------------
DROP TABLE IF EXISTS `mrosc_despesas`;
CREATE TABLE `mrosc_despesas` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `despesa_id` VARCHAR(50) NOT NULL UNIQUE,
    `projeto_id` VARCHAR(50) NOT NULL,
    `natureza_despesa` VARCHAR(20),
    `codigo_item` VARCHAR(10),
    `item_despesa` VARCHAR(255),
    `descricao` TEXT,
    `unidade` VARCHAR(50),
    `quantidade` DECIMAL(15,4) DEFAULT 0,
    `numero_meses` INT,
    `orcamento_1` DECIMAL(15,2) DEFAULT 0,
    `fornecedor_1` VARCHAR(255),
    `cnpj_fornecedor_1` VARCHAR(20),
    `orcamento_2` DECIMAL(15,2) DEFAULT 0,
    `fornecedor_2` VARCHAR(255),
    `cnpj_fornecedor_2` VARCHAR(20),
    `orcamento_3` DECIMAL(15,2) DEFAULT 0,
    `fornecedor_3` VARCHAR(255),
    `cnpj_fornecedor_3` VARCHAR(20),
    `media_orcamentos` DECIMAL(15,2) DEFAULT 0,
    `valor_unitario` DECIMAL(15,2) DEFAULT 0,
    `valor_total` DECIMAL(15,2) DEFAULT 0,
    `referencia_preco_municipal` DECIMAL(15,2),
    `fonte_referencia` VARCHAR(255),
    `observacoes` TEXT,
    `justificativa` TEXT,
    `justificativa_menor_preco` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_projeto` (`projeto_id`),
    INDEX `idx_natureza` (`natureza_despesa`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Documentos MROSC
-- ----------------------------
DROP TABLE IF EXISTS `mrosc_documentos`;
CREATE TABLE `mrosc_documentos` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `documento_id` VARCHAR(50) NOT NULL UNIQUE,
    `projeto_id` VARCHAR(50) NOT NULL,
    `despesa_id` VARCHAR(50),
    `rh_id` VARCHAR(50),
    `tipo_documento` VARCHAR(100),
    `numero_documento` VARCHAR(100),
    `data_documento` DATE,
    `valor` DECIMAL(15,2) DEFAULT 0,
    `arquivo_url` VARCHAR(500),
    `arquivo_nome` VARCHAR(255),
    `arquivo_tipo` VARCHAR(100),
    `arquivo_tamanho` INT,
    `descricao` TEXT,
    `validado` TINYINT(1) DEFAULT 0,
    `validado_por` VARCHAR(50),
    `data_validacao` DATETIME NULL,
    `observacoes_validacao` TEXT,
    `observacoes` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_projeto` (`projeto_id`),
    INDEX `idx_despesa` (`despesa_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Edições DOEM
-- ----------------------------
DROP TABLE IF EXISTS `doem_edicoes`;
CREATE TABLE `doem_edicoes` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `edicao_id` VARCHAR(50) NOT NULL UNIQUE,
    `numero_edicao` INT NOT NULL,
    `ano` VARCHAR(4),
    `data_publicacao` DATE,
    `status` VARCHAR(50) DEFAULT 'RASCUNHO',
    `publicacoes` JSON,
    `assinatura` JSON,
    `pdf_url` VARCHAR(500),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_numero` (`numero_edicao`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Newsletter DOEM
-- ----------------------------
DROP TABLE IF EXISTS `doem_newsletter`;
CREATE TABLE `doem_newsletter` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `nome` VARCHAR(255),
    `confirmado` TINYINT(1) DEFAULT 0,
    `token_confirmacao` VARCHAR(100),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `confirmed_at` DATETIME NULL,
    INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Tabela de Assinaturas de Documentos
-- ----------------------------
DROP TABLE IF EXISTS `document_signatures`;
CREATE TABLE `document_signatures` (
    `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `validation_code` VARCHAR(100) NOT NULL UNIQUE,
    `document_type` VARCHAR(100),
    `document_id` VARCHAR(50),
    `signer_name` VARCHAR(255),
    `signer_email` VARCHAR(255),
    `signer_cpf` VARCHAR(14),
    `signature_data` TEXT,
    `signed_at` DATETIME,
    `ip_address` VARCHAR(45),
    `user_agent` TEXT,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_code` (`validation_code`),
    INDEX `idx_document` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
