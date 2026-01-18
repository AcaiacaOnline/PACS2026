<?php
/**
 * Planejamento Acaiaca - Instalador para cPanel
 * Sistema de Gestão Municipal
 * 
 * Similar ao instalador do WordPress, este script configura automaticamente
 * o sistema em hospedagem compartilhada com cPanel/MySQL.
 * 
 * Requisitos:
 * - PHP 7.4+
 * - MySQL 5.7+ ou MariaDB 10.3+
 * - Extensões: PDO, PDO_MySQL, JSON, mbstring
 */

// Configurações de erro para instalação
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Constantes
define('INSTALLER_VERSION', '1.0.0');
define('MIN_PHP_VERSION', '7.4.0');
define('MIN_MYSQL_VERSION', '5.7.0');

// Verificar requisitos
function check_requirements() {
    $errors = [];
    
    // PHP Version
    if (version_compare(PHP_VERSION, MIN_PHP_VERSION, '<')) {
        $errors[] = "PHP " . MIN_PHP_VERSION . " ou superior é necessário. Versão atual: " . PHP_VERSION;
    }
    
    // Required extensions
    $required_extensions = ['pdo', 'pdo_mysql', 'json', 'mbstring'];
    foreach ($required_extensions as $ext) {
        if (!extension_loaded($ext)) {
            $errors[] = "Extensão PHP '$ext' não está instalada.";
        }
    }
    
    // Write permissions
    $dirs_to_check = ['.', './uploads', './config'];
    foreach ($dirs_to_check as $dir) {
        if (file_exists($dir) && !is_writable($dir)) {
            $errors[] = "Diretório '$dir' não tem permissão de escrita.";
        }
    }
    
    return $errors;
}

// Testar conexão com banco de dados
function test_database_connection($host, $name, $user, $pass) {
    try {
        $dsn = "mysql:host=$host;dbname=$name;charset=utf8mb4";
        $pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
        ]);
        
        // Verificar versão do MySQL
        $version = $pdo->query("SELECT VERSION()")->fetchColumn();
        
        return ['success' => true, 'version' => $version, 'pdo' => $pdo];
    } catch (PDOException $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

// Executar schema SQL
function execute_schema($pdo, $schema_file) {
    try {
        if (!file_exists($schema_file)) {
            return ['success' => false, 'error' => "Arquivo schema.sql não encontrado."];
        }
        
        $sql = file_get_contents($schema_file);
        
        // Dividir em comandos individuais
        $commands = array_filter(
            array_map('trim', explode(';', $sql)),
            function($cmd) { return !empty($cmd) && !preg_match('/^--/', $cmd); }
        );
        
        $executed = 0;
        foreach ($commands as $command) {
            if (!empty(trim($command))) {
                $pdo->exec($command);
                $executed++;
            }
        }
        
        return ['success' => true, 'executed' => $executed];
    } catch (PDOException $e) {
        return ['success' => false, 'error' => $e->getMessage()];
    }
}

// Criar arquivo de configuração
function create_config_file($config) {
    $config_content = "<?php\n";
    $config_content .= "// Configuração do Planejamento Acaiaca\n";
    $config_content .= "// Gerado automaticamente pelo instalador em " . date('Y-m-d H:i:s') . "\n\n";
    $config_content .= "define('DB_HOST', '" . addslashes($config['db_host']) . "');\n";
    $config_content .= "define('DB_NAME', '" . addslashes($config['db_name']) . "');\n";
    $config_content .= "define('DB_USER', '" . addslashes($config['db_user']) . "');\n";
    $config_content .= "define('DB_PASS', '" . addslashes($config['db_pass']) . "');\n\n";
    $config_content .= "define('SITE_URL', '" . addslashes($config['site_url']) . "');\n";
    $config_content .= "define('ADMIN_EMAIL', '" . addslashes($config['admin_email']) . "');\n\n";
    $config_content .= "define('JWT_SECRET', '" . bin2hex(random_bytes(32)) . "');\n";
    $config_content .= "define('INSTALLED', true);\n";
    $config_content .= "define('VERSION', '" . INSTALLER_VERSION . "');\n";
    
    // Criar diretório config se não existir
    if (!file_exists('./config')) {
        mkdir('./config', 0755, true);
    }
    
    if (file_put_contents('./config/config.php', $config_content)) {
        return ['success' => true];
    } else {
        return ['success' => false, 'error' => 'Não foi possível criar o arquivo de configuração.'];
    }
}

// Criar diretórios necessários
function create_directories() {
    $dirs = [
        './uploads',
        './uploads/mrosc',
        './uploads/doem',
        './uploads/temp',
        './config',
        './logs'
    ];
    
    foreach ($dirs as $dir) {
        if (!file_exists($dir)) {
            mkdir($dir, 0755, true);
        }
    }
    
    // Criar .htaccess para proteção
    $htaccess_content = "Options -Indexes\n";
    $htaccess_content .= "Order Allow,Deny\n";
    $htaccess_content .= "Deny from all\n";
    
    file_put_contents('./uploads/.htaccess', $htaccess_content);
    file_put_contents('./config/.htaccess', $htaccess_content);
    file_put_contents('./logs/.htaccess', $htaccess_content);
    
    return true;
}

// Processar formulário de instalação
$step = isset($_GET['step']) ? (int)$_GET['step'] : 1;
$errors = [];
$success = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    switch ($step) {
        case 2: // Verificar banco de dados
            $db_result = test_database_connection(
                $_POST['db_host'],
                $_POST['db_name'],
                $_POST['db_user'],
                $_POST['db_pass']
            );
            
            if ($db_result['success']) {
                $_SESSION['db_config'] = [
                    'host' => $_POST['db_host'],
                    'name' => $_POST['db_name'],
                    'user' => $_POST['db_user'],
                    'pass' => $_POST['db_pass']
                ];
                header('Location: ?step=3');
                exit;
            } else {
                $errors[] = "Erro na conexão: " . $db_result['error'];
            }
            break;
            
        case 3: // Instalar banco de dados e configurar
            session_start();
            $db_config = $_SESSION['db_config'] ?? null;
            
            if (!$db_config) {
                header('Location: ?step=2');
                exit;
            }
            
            // Conectar ao banco
            $db_result = test_database_connection(
                $db_config['host'],
                $db_config['name'],
                $db_config['user'],
                $db_config['pass']
            );
            
            if (!$db_result['success']) {
                $errors[] = "Erro na conexão: " . $db_result['error'];
                break;
            }
            
            // Executar schema
            $schema_result = execute_schema($db_result['pdo'], './schema.sql');
            if (!$schema_result['success']) {
                $errors[] = "Erro ao criar tabelas: " . $schema_result['error'];
                break;
            }
            
            // Criar arquivo de configuração
            $config = [
                'db_host' => $db_config['host'],
                'db_name' => $db_config['name'],
                'db_user' => $db_config['user'],
                'db_pass' => $db_config['pass'],
                'site_url' => $_POST['site_url'],
                'admin_email' => $_POST['admin_email']
            ];
            
            $config_result = create_config_file($config);
            if (!$config_result['success']) {
                $errors[] = $config_result['error'];
                break;
            }
            
            // Criar diretórios
            create_directories();
            
            $success = true;
            break;
    }
}

// Se já está instalado, redirecionar
if (file_exists('./config/config.php')) {
    include './config/config.php';
    if (defined('INSTALLED') && INSTALLED) {
        // Já instalado
        ?>
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Planejamento Acaiaca - Já Instalado</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
                .container { max-width: 600px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #1F4E78; }
                .success { background: #E8F5E9; padding: 15px; border-radius: 4px; margin: 20px 0; }
                a { color: #1F4E78; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ Sistema Já Instalado</h1>
                <div class="success">
                    <p>O Planejamento Acaiaca já está instalado e configurado.</p>
                    <p><a href="index.php">Ir para o sistema</a></p>
                </div>
                <p><small>Para reinstalar, remova o arquivo <code>config/config.php</code></small></p>
            </div>
        </body>
        </html>
        <?php
        exit;
    }
}

// Verificar requisitos iniciais
$requirements_errors = check_requirements();
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Planejamento Acaiaca - Instalação</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1F4E78, #2E7D32);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 {
            color: #1F4E78;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .steps {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .step {
            text-align: center;
            flex: 1;
        }
        .step-number {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e0e0e0;
            color: #666;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .step.active .step-number {
            background: #1F4E78;
            color: white;
        }
        .step.completed .step-number {
            background: #2E7D32;
            color: white;
        }
        .step-title {
            font-size: 12px;
            color: #666;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        input[type="text"],
        input[type="password"],
        input[type="email"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            border-color: #1F4E78;
            outline: none;
        }
        .btn {
            background: #1F4E78;
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #163a5a;
        }
        .btn-success {
            background: #2E7D32;
        }
        .btn-success:hover {
            background: #1b5e20;
        }
        .error {
            background: #FFEBEE;
            border: 1px solid #EF5350;
            color: #C62828;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .success {
            background: #E8F5E9;
            border: 1px solid #66BB6A;
            color: #2E7D32;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .info {
            background: #E3F2FD;
            border: 1px solid #42A5F5;
            color: #1565C0;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .requirements {
            list-style: none;
            padding: 0;
        }
        .requirements li {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .requirements li:before {
            content: '✓';
            color: #2E7D32;
            margin-right: 10px;
        }
        .requirements li.error:before {
            content: '✗';
            color: #C62828;
        }
        .hint {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ Planejamento Acaiaca</h1>
        <p class="subtitle">Sistema de Gestão Municipal - Instalação v<?php echo INSTALLER_VERSION; ?></p>
        
        <div class="steps">
            <div class="step <?php echo $step >= 1 ? ($step > 1 ? 'completed' : 'active') : ''; ?>">
                <div class="step-number">1</div>
                <div class="step-title">Requisitos</div>
            </div>
            <div class="step <?php echo $step >= 2 ? ($step > 2 ? 'completed' : 'active') : ''; ?>">
                <div class="step-number">2</div>
                <div class="step-title">Banco de Dados</div>
            </div>
            <div class="step <?php echo $step >= 3 ? ($step > 3 ? 'completed' : 'active') : ''; ?>">
                <div class="step-number">3</div>
                <div class="step-title">Configuração</div>
            </div>
            <div class="step <?php echo $success ? 'active' : ''; ?>">
                <div class="step-number">4</div>
                <div class="step-title">Conclusão</div>
            </div>
        </div>
        
        <?php if (!empty($errors)): ?>
            <div class="error">
                <?php foreach ($errors as $error): ?>
                    <p><?php echo htmlspecialchars($error); ?></p>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
        
        <?php if ($success): ?>
            <div class="success">
                <h2>✅ Instalação Concluída!</h2>
                <p>O Planejamento Acaiaca foi instalado com sucesso.</p>
                <p><strong>Credenciais de acesso:</strong></p>
                <ul>
                    <li>Email: admin@acaiaca.mg.gov.br</li>
                    <li>Senha: Admin@123</li>
                </ul>
                <p><strong>⚠️ Importante:</strong> Altere a senha padrão após o primeiro login!</p>
            </div>
            <p><a href="index.php" class="btn btn-success">Acessar o Sistema →</a></p>
            <p style="margin-top: 20px;"><small>Por segurança, remova ou renomeie este arquivo (install.php) após a instalação.</small></p>
            
        <?php elseif ($step === 1): ?>
            <h2>Verificação de Requisitos</h2>
            
            <?php if (!empty($requirements_errors)): ?>
                <div class="error">
                    <p><strong>Os seguintes requisitos não foram atendidos:</strong></p>
                    <ul>
                        <?php foreach ($requirements_errors as $error): ?>
                            <li><?php echo htmlspecialchars($error); ?></li>
                        <?php endforeach; ?>
                    </ul>
                </div>
            <?php else: ?>
                <div class="success">
                    <p>Todos os requisitos foram atendidos!</p>
                </div>
                <ul class="requirements">
                    <li>PHP <?php echo PHP_VERSION; ?> ✓</li>
                    <li>Extensão PDO ✓</li>
                    <li>Extensão PDO_MySQL ✓</li>
                    <li>Extensão JSON ✓</li>
                    <li>Extensão mbstring ✓</li>
                </ul>
                <p><a href="?step=2" class="btn">Continuar →</a></p>
            <?php endif; ?>
            
        <?php elseif ($step === 2): ?>
            <h2>Configuração do Banco de Dados</h2>
            <div class="info">
                <p>Informe os dados de conexão com o banco de dados MySQL.</p>
                <p>Você pode criar um banco de dados no cPanel em: "Bancos de Dados MySQL"</p>
            </div>
            
            <form method="POST">
                <div class="form-group">
                    <label>Host do Banco de Dados</label>
                    <input type="text" name="db_host" value="localhost" required>
                    <div class="hint">Geralmente é "localhost" em hospedagens cPanel</div>
                </div>
                
                <div class="form-group">
                    <label>Nome do Banco de Dados</label>
                    <input type="text" name="db_name" required placeholder="Ex: usuario_pacaiaca">
                </div>
                
                <div class="form-group">
                    <label>Usuário do Banco de Dados</label>
                    <input type="text" name="db_user" required placeholder="Ex: usuario_admin">
                </div>
                
                <div class="form-group">
                    <label>Senha do Banco de Dados</label>
                    <input type="password" name="db_pass" required>
                </div>
                
                <button type="submit" class="btn">Testar Conexão e Continuar →</button>
            </form>
            
        <?php elseif ($step === 3): ?>
            <?php session_start(); ?>
            <h2>Configuração do Sistema</h2>
            
            <form method="POST">
                <div class="form-group">
                    <label>URL do Site</label>
                    <input type="text" name="site_url" required placeholder="https://seudominio.com.br" 
                           value="<?php echo 'https://' . $_SERVER['HTTP_HOST']; ?>">
                    <div class="hint">URL completa onde o sistema será acessado</div>
                </div>
                
                <div class="form-group">
                    <label>Email do Administrador</label>
                    <input type="email" name="admin_email" required placeholder="admin@seudominio.com.br">
                    <div class="hint">Email para notificações do sistema</div>
                </div>
                
                <button type="submit" class="btn btn-success">Instalar Sistema →</button>
            </form>
        <?php endif; ?>
    </div>
</body>
</html>
