<?php
/**
 * PAC Acaiaca 2026 - Instalador Web
 * Desenvolvido por Cristiano Abdo de Souza - Assessor de Planejamento, Compras e Logística
 */

$step = $_GET['step'] ?? 1;
$error = '';
$success = '';

// Processar instalação
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($step == 2) {
        // Testar conexão com banco
        $dbHost = $_POST['db_host'];
        $dbName = $_POST['db_name'];
        $dbUser = $_POST['db_user'];
        $dbPass = $_POST['db_pass'];
        
        try {
            $conn = new PDO("mysql:host=$dbHost", $dbUser, $dbPass);
            $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            
            // Criar banco se não existir
            $conn->exec("CREATE DATABASE IF NOT EXISTS `$dbName` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
            $conn->exec("USE `$dbName`");
            
            // Criar tabelas
            $sql = file_get_contents(__DIR__ . '/schema.sql');
            $conn->exec($sql);
            
            // Criar usuário admin
            $adminPass = password_hash('Cris@820906', PASSWORD_BCRYPT);
            $userId = 'user_' . bin2hex(random_bytes(6));
            
            $stmt = $conn->prepare(
                "INSERT INTO users (user_id, email, name, password_hash, is_admin, is_active, created_at) 
                 VALUES (?, ?, ?, ?, 1, 1, NOW())"
            );
            $stmt->execute([$userId, 'cristiano.abdo@acaiaca.mg.gov.br', 'Cristiano Abdo de Souza', $adminPass]);
            
            // Criar arquivo config.php
            $jwtSecret = bin2hex(random_bytes(32));
            $baseUrl = $_POST['base_url'];
            
            $configContent = "<?php\n";
            $configContent .= "define('DB_HOST', '$dbHost');\n";
            $configContent .= "define('DB_NAME', '$dbName');\n";
            $configContent .= "define('DB_USER', '$dbUser');\n";
            $configContent .= "define('DB_PASS', '$dbPass');\n";
            $configContent .= "define('DB_CHARSET', 'utf8mb4');\n";
            $configContent .= "define('JWT_SECRET', '$jwtSecret');\n";
            $configContent .= "define('JWT_EXPIRATION', 7 * 24 * 60 * 60);\n";
            $configContent .= "define('BASE_URL', '$baseUrl');\n";
            $configContent .= "date_default_timezone_set('America/Sao_Paulo');\n";
            $configContent .= "ini_set('display_errors', 0);\n";
            $configContent .= "ini_set('log_errors', 1);\n";
            $configContent .= "error_reporting(E_ALL);\n";
            $configContent .= "?>";
            
            file_put_contents(__DIR__ . '/../config.php', $configContent);
            
            // Criar .htaccess
            $htaccess = "# PAC Acaiaca 2026\n";
            $htaccess .= "RewriteEngine On\n";
            $htaccess .= "RewriteBase /\n\n";
            $htaccess .= "# Redirecionar API para api/\n";
            $htaccess .= "RewriteRule ^api/(.*)$ api/$1 [L]\n\n";
            $htaccess .= "# Single Page Application - redirecionar tudo para index.html\n";
            $htaccess .= "RewriteCond %{REQUEST_FILENAME} !-f\n";
            $htaccess .= "RewriteCond %{REQUEST_FILENAME} !-d\n";
            $htaccess .= "RewriteRule . /index.html [L]\n\n";
            $htaccess .= "# Headers de segurança\n";
            $htaccess .= "<IfModule mod_headers.c>\n";
            $htaccess .= "    Header set X-Content-Type-Options \"nosniff\"\n";
            $htaccess .= "    Header set X-Frame-Options \"SAMEORIGIN\"\n";
            $htaccess .= "    Header set X-XSS-Protection \"1; mode=block\"\n";
            $htaccess .= "</IfModule>\n";
            
            file_put_contents(__DIR__ . '/../.htaccess', $htaccess);
            
            $success = "Instalação concluída com sucesso!";
            $step = 3;
            
        } catch(PDOException $e) {
            $error = "Erro ao conectar: " . $e->getMessage();
        }
    }
}
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instalador PAC Acaiaca 2026</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo h1 {
            color: #1a365d;
            font-size: 28px;
            margin-bottom: 5px;
        }
        .logo p {
            color: #718096;
            font-size: 14px;
        }
        .steps {
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            position: relative;
        }
        .steps::before {
            content: '';
            position: absolute;
            top: 15px;
            left: 0;
            right: 0;
            height: 2px;
            background: #e2e8f0;
            z-index: 0;
        }
        .step {
            background: white;
            position: relative;
            z-index: 1;
            text-align: center;
            flex: 1;
        }
        .step-circle {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #e2e8f0;
            color: #a0aec0;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 10px;
            font-weight: bold;
        }
        .step.active .step-circle {
            background: #4299e1;
            color: white;
        }
        .step.completed .step-circle {
            background: #48bb78;
            color: white;
        }
        .step-label {
            font-size: 12px;
            color: #718096;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2d3748;
        }
        input[type="text"],
        input[type="password"],
        input[type="email"],
        input[type="url"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #e2e8f0;
            border-radius: 5px;
            font-size: 14px;
        }
        input:focus {
            outline: none;
            border-color: #4299e1;
        }
        .btn {
            background: #4299e1;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
        }
        .btn:hover {
            background: #3182ce;
        }
        .alert {
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .alert-error {
            background: #fed7d7;
            color: #c53030;
            border: 1px solid #fc8181;
        }
        .alert-success {
            background: #c6f6d5;
            color: #22543d;
            border: 1px solid #68d391;
        }
        .info-box {
            background: #ebf8ff;
            border: 1px solid #90cdf4;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .info-box strong {
            color: #2c5282;
        }
        .success-icon {
            text-align: center;
            font-size: 60px;
            color: #48bb78;
            margin-bottom: 20px;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #718096;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>🛒 PAC Acaiaca 2026</h1>
            <p>Instalador do Sistema</p>
        </div>
        
        <div class="steps">
            <div class="step <?= $step >= 1 ? 'active' : '' ?> <?= $step > 1 ? 'completed' : '' ?>">
                <div class="step-circle">1</div>
                <div class="step-label">Bem-vindo</div>
            </div>
            <div class="step <?= $step >= 2 ? 'active' : '' ?> <?= $step > 2 ? 'completed' : '' ?>">
                <div class="step-circle">2</div>
                <div class="step-label">Configuração</div>
            </div>
            <div class="step <?= $step >= 3 ? 'active' : '' ?>">
                <div class="step-circle">3</div>
                <div class="step-label">Concluído</div>
            </div>
        </div>
        
        <?php if ($error): ?>
            <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        
        <?php if ($success): ?>
            <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
        <?php endif; ?>
        
        <?php if ($step == 1): ?>
            <h2 style="margin-bottom: 20px;">Bem-vindo ao Instalador</h2>
            <p style="margin-bottom: 20px; color: #718096;">
                Este assistente irá guiá-lo através da instalação do Sistema PAC Acaiaca 2026.
            </p>
            
            <div class="info-box">
                <strong>Requisitos:</strong>
                <ul style="margin-left: 20px; margin-top: 10px; color: #4a5568;">
                    <li>PHP 7.4 ou superior</li>
                    <li>MySQL 5.7 ou superior</li>
                    <li>Extensões: PDO, PDO_MySQL, mbstring, json</li>
                    <li>Permissões de escrita no diretório</li>
                </ul>
            </div>
            
            <a href="?step=2" class="btn">Iniciar Instalação</a>
            
        <?php elseif ($step == 2): ?>
            <h2 style="margin-bottom: 20px;">Configuração do Banco de Dados</h2>
            
            <form method="POST">
                <div class="form-group">
                    <label>Host do Banco de Dados</label>
                    <input type="text" name="db_host" value="localhost" required>
                </div>
                
                <div class="form-group">
                    <label>Nome do Banco de Dados</label>
                    <input type="text" name="db_name" value="pac_acaiaca" required>
                </div>
                
                <div class="form-group">
                    <label>Usuário do Banco</label>
                    <input type="text" name="db_user" required>
                </div>
                
                <div class="form-group">
                    <label>Senha do Banco</label>
                    <input type="password" name="db_pass">
                </div>
                
                <div class="form-group">
                    <label>URL do Sistema</label>
                    <input type="url" name="base_url" value="https://pac.acaiaca.mg.gov.br" required>
                </div>
                
                <button type="submit" class="btn">Instalar Sistema</button>
            </form>
            
        <?php elseif ($step == 3): ?>
            <div class="success-icon">✅</div>
            <h2 style="text-align: center; margin-bottom: 20px; color: #22543d;">Instalação Concluída!</h2>
            
            <div class="info-box">
                <strong>Credenciais de Acesso:</strong>
                <ul style="margin-left: 20px; margin-top: 10px; color: #4a5568;">
                    <li><strong>Email:</strong> cristiano.abdo@acaiaca.mg.gov.br</li>
                    <li><strong>Senha:</strong> Cris@820906</li>
                </ul>
                <p style="margin-top: 10px; color: #c53030;">
                    <strong>⚠️ IMPORTANTE:</strong> Altere a senha após o primeiro login!
                </p>
            </div>
            
            <div class="alert alert-success" style="margin-top: 20px;">
                <strong>Próximos Passos:</strong><br>
                1. Remova ou renomeie a pasta /install por segurança<br>
                2. Faça login no sistema<br>
                3. Configure os usuários adicionais
            </div>
            
            <a href="../" class="btn">Acessar o Sistema</a>
        <?php endif; ?>
        
        <div class="footer">
            Desenvolvido por Cristiano Abdo de Souza<br>
            Assessor de Planejamento, Compras e Logística
        </div>
    </div>
</body>
</html>
