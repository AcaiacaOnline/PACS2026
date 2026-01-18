<?php
/**
 * Planejamento Acaiaca - Instalador cPanel
 * Similar ao instalador do WordPress
 */

// Verificar se já foi instalado
if (file_exists('.installed')) {
    die('<h1>Sistema já instalado!</h1><p>Por segurança, remova o arquivo install.php</p>');
}

// Funções auxiliares
function sanitize($str) {
    return htmlspecialchars(trim($str), ENT_QUOTES, 'UTF-8');
}

function generateSecret($length = 64) {
    return bin2hex(random_bytes($length / 2));
}

function testConnection($host, $user, $pass, $db, $port = 3306) {
    try {
        $dsn = "mysql:host=$host;port=$port;dbname=$db;charset=utf8mb4";
        $pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
        ]);
        return ['success' => true, 'pdo' => $pdo];
    } catch (PDOException $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

function createTables($pdo) {
    $sql = file_get_contents(__DIR__ . '/schema.sql');
    $pdo->exec($sql);
    return true;
}

function createAdmin($pdo, $name, $email, $password) {
    $userId = 'user_' . substr(md5(uniqid()), 0, 12);
    $hash = password_hash($password, PASSWORD_BCRYPT);
    
    $stmt = $pdo->prepare("
        INSERT INTO users (user_id, email, name, password_hash, is_admin, is_active, tipo_usuario)
        VALUES (?, ?, ?, ?, 1, 1, 'servidor')
    ");
    $stmt->execute([$userId, $email, $name, $hash]);
    return true;
}

function createEnvFile($config) {
    $env = "# Planejamento Acaiaca - Configuração
# Gerado em: " . date('Y-m-d H:i:s') . "

# Banco de Dados
DB_HOST={$config['db_host']}
DB_PORT={$config['db_port']}
DB_NAME={$config['db_name']}
DB_USER={$config['db_user']}
DB_PASSWORD={$config['db_pass']}

# Aplicação
APP_URL={$config['app_url']}
APP_ENV=production
APP_DEBUG=false

# Segurança
JWT_SECRET={$config['jwt_secret']}

# Prefeitura
PREFEITURA_NOME={$config['prefeitura_nome']}
PREFEITURA_CNPJ={$config['prefeitura_cnpj']}
";
    return file_put_contents('.env', $env);
}

// Processar instalação
$step = isset($_GET['step']) ? (int)$_GET['step'] : 1;
$error = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if ($step === 2) {
        // Testar conexão com banco
        $result = testConnection(
            $_POST['db_host'],
            $_POST['db_user'],
            $_POST['db_pass'],
            $_POST['db_name'],
            $_POST['db_port']
        );
        
        if ($result['success']) {
            $_SESSION['db_config'] = $_POST;
            $_SESSION['pdo'] = $result['pdo'];
            header('Location: install.php?step=3');
            exit;
        } else {
            $error = 'Erro na conexão: ' . $result['error'];
        }
    }
    
    if ($step === 3) {
        // Criar tabelas e admin
        try {
            session_start();
            $dsn = "mysql:host={$_SESSION['db_config']['db_host']};port={$_SESSION['db_config']['db_port']};dbname={$_SESSION['db_config']['db_name']};charset=utf8mb4";
            $pdo = new PDO($dsn, $_SESSION['db_config']['db_user'], $_SESSION['db_config']['db_pass']);
            
            createTables($pdo);
            createAdmin($pdo, $_POST['admin_name'], $_POST['admin_email'], $_POST['admin_password']);
            
            $config = [
                'db_host' => $_SESSION['db_config']['db_host'],
                'db_port' => $_SESSION['db_config']['db_port'],
                'db_name' => $_SESSION['db_config']['db_name'],
                'db_user' => $_SESSION['db_config']['db_user'],
                'db_pass' => $_SESSION['db_config']['db_pass'],
                'app_url' => $_POST['app_url'],
                'jwt_secret' => generateSecret(),
                'prefeitura_nome' => $_POST['prefeitura_nome'],
                'prefeitura_cnpj' => $_POST['prefeitura_cnpj']
            ];
            
            createEnvFile($config);
            
            // Criar diretório de uploads
            if (!is_dir('uploads')) {
                mkdir('uploads', 0755, true);
            }
            
            // Marcar como instalado
            file_put_contents('.installed', date('Y-m-d H:i:s'));
            
            header('Location: install.php?step=4');
            exit;
        } catch (Exception $e) {
            $error = 'Erro na instalação: ' . $e->getMessage();
        }
    }
}
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instalação - Planejamento Acaiaca</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1F4E78 0%, #2E7D32 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            overflow: hidden;
        }
        .header {
            background: #1F4E78;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.8; font-size: 14px; }
        .content { padding: 30px; }
        .steps {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 30px;
        }
        .step-indicator {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            background: #e0e0e0;
            color: #666;
        }
        .step-indicator.active { background: #1F4E78; color: white; }
        .step-indicator.done { background: #2E7D32; color: white; }
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        .form-group input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #1F4E78;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .btn {
            display: inline-block;
            padding: 14px 30px;
            background: #1F4E78;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            width: 100%;
        }
        .btn:hover { background: #163a5c; }
        .btn-success { background: #2E7D32; }
        .btn-success:hover { background: #1b5e20; }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .alert-error { background: #ffebee; color: #c62828; border: 1px solid #ef9a9a; }
        .alert-success { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
        .success-icon {
            font-size: 80px;
            color: #2E7D32;
            margin-bottom: 20px;
        }
        .info-box {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .info-box h3 { margin-bottom: 10px; color: #333; }
        .info-box p { color: #666; font-size: 14px; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Planejamento Acaiaca</h1>
            <p>Sistema de Gestão Municipal</p>
        </div>
        
        <div class="content">
            <div class="steps">
                <div class="step-indicator <?= $step >= 1 ? ($step > 1 ? 'done' : 'active') : '' ?>">1</div>
                <div class="step-indicator <?= $step >= 2 ? ($step > 2 ? 'done' : 'active') : '' ?>">2</div>
                <div class="step-indicator <?= $step >= 3 ? ($step > 3 ? 'done' : 'active') : '' ?>">3</div>
                <div class="step-indicator <?= $step >= 4 ? 'active' : '' ?>">4</div>
            </div>
            
            <?php if ($error): ?>
                <div class="alert alert-error"><?= sanitize($error) ?></div>
            <?php endif; ?>
            
            <?php if ($step === 1): ?>
                <!-- Passo 1: Boas-vindas -->
                <h2 style="margin-bottom: 20px;">Bem-vindo ao Instalador</h2>
                <p style="color: #666; margin-bottom: 30px;">
                    Este assistente irá guiá-lo através do processo de instalação do 
                    Sistema de Gestão Municipal - Planejamento Acaiaca.
                </p>
                
                <div class="info-box">
                    <h3>📋 Requisitos</h3>
                    <p>
                        • PHP 8.1 ou superior<br>
                        • MySQL 8.0 / MariaDB 10.5<br>
                        • Extensões: pdo_mysql, mbstring, json<br>
                        • 512MB de memória RAM
                    </p>
                </div>
                
                <div style="margin-top: 30px;">
                    <a href="install.php?step=2" class="btn">Iniciar Instalação →</a>
                </div>
                
            <?php elseif ($step === 2): ?>
                <!-- Passo 2: Banco de Dados -->
                <h2 style="margin-bottom: 20px;">Configuração do Banco de Dados</h2>
                <form method="POST">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Host do Banco</label>
                            <input type="text" name="db_host" value="localhost" required>
                        </div>
                        <div class="form-group">
                            <label>Porta</label>
                            <input type="text" name="db_port" value="3306" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Nome do Banco de Dados</label>
                        <input type="text" name="db_name" placeholder="planejamento_acaiaca" required>
                    </div>
                    <div class="form-group">
                        <label>Usuário do Banco</label>
                        <input type="text" name="db_user" required>
                    </div>
                    <div class="form-group">
                        <label>Senha do Banco</label>
                        <input type="password" name="db_pass" required>
                    </div>
                    <button type="submit" class="btn">Testar Conexão →</button>
                </form>
                
            <?php elseif ($step === 3): ?>
                <!-- Passo 3: Configurações -->
                <h2 style="margin-bottom: 20px;">Configurações do Sistema</h2>
                <form method="POST">
                    <h3 style="margin-bottom: 15px; color: #1F4E78;">👤 Administrador</h3>
                    <div class="form-group">
                        <label>Nome Completo</label>
                        <input type="text" name="admin_name" required>
                    </div>
                    <div class="form-group">
                        <label>E-mail</label>
                        <input type="email" name="admin_email" required>
                    </div>
                    <div class="form-group">
                        <label>Senha (mínimo 8 caracteres)</label>
                        <input type="password" name="admin_password" minlength="8" required>
                    </div>
                    
                    <h3 style="margin: 25px 0 15px; color: #1F4E78;">🏛️ Prefeitura</h3>
                    <div class="form-group">
                        <label>Nome da Prefeitura</label>
                        <input type="text" name="prefeitura_nome" value="Prefeitura Municipal de Acaiaca" required>
                    </div>
                    <div class="form-group">
                        <label>CNPJ</label>
                        <input type="text" name="prefeitura_cnpj" value="18.295.287/0001-90">
                    </div>
                    <div class="form-group">
                        <label>URL do Sistema</label>
                        <input type="url" name="app_url" value="<?= 'https://' . $_SERVER['HTTP_HOST'] ?>" required>
                    </div>
                    
                    <button type="submit" class="btn btn-success">Instalar Sistema →</button>
                </form>
                
            <?php elseif ($step === 4): ?>
                <!-- Passo 4: Sucesso -->
                <div style="text-align: center;">
                    <div class="success-icon">✅</div>
                    <h2 style="margin-bottom: 15px; color: #2E7D32;">Instalação Concluída!</h2>
                    <p style="color: #666; margin-bottom: 30px;">
                        O sistema foi instalado com sucesso. Você já pode acessar o painel administrativo.
                    </p>
                    
                    <div class="alert alert-error" style="text-align: left;">
                        <strong>⚠️ IMPORTANTE:</strong> Por segurança, remova o arquivo <code>install.php</code> do servidor.
                    </div>
                    
                    <a href="/" class="btn btn-success">Acessar o Sistema →</a>
                </div>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>
