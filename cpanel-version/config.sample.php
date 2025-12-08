<?php
// PAC Acaiaca 2026 - Arquivo de Configuração
// Renomeie este arquivo para config.php e ajuste as configurações

define('DB_HOST', 'localhost');
define('DB_NAME', 'pac_acaiaca');
define('DB_USER', 'seu_usuario');
define('DB_PASS', 'sua_senha');
define('DB_CHARSET', 'utf8mb4');

// Chave secreta para JWT (gere uma aleatória)
define('JWT_SECRET', 'MUDE_ESTA_CHAVE_PARA_UMA_ALEATORIA_E_SEGURA');
define('JWT_EXPIRATION', 7 * 24 * 60 * 60); // 7 dias

// URL base do sistema
define('BASE_URL', 'https://pac.acaiaca.mg.gov.br');

// Timezone
date_default_timezone_set('America/Sao_Paulo');

// Configurações de erro (desative em produção)
ini_set('display_errors', 0);
ini_set('log_errors', 1);
error_reporting(E_ALL);

// Configurações de sessão
ini_set('session.cookie_httponly', 1);
ini_set('session.use_only_cookies', 1);
ini_set('session.cookie_secure', 1);
ini_set('session.cookie_samesite', 'Lax');
?>