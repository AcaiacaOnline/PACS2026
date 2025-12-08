-- PAC Acaiaca 2026 - Schema do Banco de Dados
-- Desenvolvido por Cristiano Abdo de Souza

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` VARCHAR(50) UNIQUE NOT NULL,
  `email` VARCHAR(255) UNIQUE NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `password_hash` VARCHAR(255),
  `is_admin` TINYINT(1) DEFAULT 0,
  `is_active` TINYINT(1) DEFAULT 1,
  `picture` VARCHAR(500),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Sessões (opcional, para OAuth)
CREATE TABLE IF NOT EXISTS `user_sessions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` VARCHAR(50) NOT NULL,
  `session_token` VARCHAR(500) NOT NULL,
  `expires_at` DATETIME NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_session_token` (`session_token`(100)),
  INDEX `idx_user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de PACs
CREATE TABLE IF NOT EXISTS `pacs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `pac_id` VARCHAR(50) UNIQUE NOT NULL,
  `user_id` VARCHAR(50) NOT NULL,
  `secretaria` VARCHAR(255) NOT NULL,
  `secretario` VARCHAR(255) NOT NULL,
  `fiscal` VARCHAR(255),
  `telefone` VARCHAR(50),
  `email` VARCHAR(255),
  `endereco` TEXT,
  `ano` VARCHAR(4) DEFAULT '2026',
  `total_value` DECIMAL(15,2) DEFAULT 0.00,
  `stats_consumo` DECIMAL(15,2) DEFAULT 0.00,
  `stats_consumo_qtd` INT DEFAULT 0,
  `stats_permanente` DECIMAL(15,2) DEFAULT 0.00,
  `stats_permanente_qtd` INT DEFAULT 0,
  `stats_servicos` DECIMAL(15,2) DEFAULT 0.00,
  `stats_servicos_qtd` INT DEFAULT 0,
  `stats_obras` DECIMAL(15,2) DEFAULT 0.00,
  `stats_obras_qtd` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_pac_id` (`pac_id`),
  INDEX `idx_user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de Itens do PAC
CREATE TABLE IF NOT EXISTS `pac_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `item_id` VARCHAR(50) UNIQUE NOT NULL,
  `pac_id` VARCHAR(50) NOT NULL,
  `tipo` VARCHAR(100) NOT NULL,
  `catmat` VARCHAR(50),
  `descricao` TEXT NOT NULL,
  `unidade` VARCHAR(50) NOT NULL,
  `quantidade` DECIMAL(10,2) NOT NULL,
  `valorUnitario` DECIMAL(15,2) NOT NULL,
  `valorTotal` DECIMAL(15,2) NOT NULL,
  `prioridade` VARCHAR(20) NOT NULL,
  `justificativa` TEXT,
  `imagemUrl` VARCHAR(500),
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_item_id` (`item_id`),
  INDEX `idx_pac_id` (`pac_id`),
  FOREIGN KEY (`pac_id`) REFERENCES `pacs`(`pac_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
