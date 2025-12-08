<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Access-Control-Allow-Credentials: true');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../includes/Database.php';
require_once __DIR__ . '/../includes/Auth.php';

// Roteamento simples
$requestUri = $_SERVER['REQUEST_URI'];
$scriptName = dirname($_SERVER['SCRIPT_NAME']);
$uri = str_replace($scriptName, '', $requestUri);
$uri = trim($uri, '/');
$uri = explode('?', $uri)[0];

$method = $_SERVER['REQUEST_METHOD'];
$parts = explode('/', $uri);

// Remover 'api' se estiver presente
if ($parts[0] === 'api') {
    array_shift($parts);
}

$endpoint = $parts[0] ?? '';
$resource = $parts[1] ?? '';
$id = $parts[2] ?? '';

try {
    // Rotas de Autenticação
    if ($endpoint === 'auth') {
        require_once __DIR__ . '/auth.php';
    }
    // Rotas de Usuários
    elseif ($endpoint === 'users') {
        require_once __DIR__ . '/users.php';
    }
    // Rotas de PACs
    elseif ($endpoint === 'pacs') {
        require_once __DIR__ . '/pacs.php';
    }
    // Rotas de Dashboard
    elseif ($endpoint === 'dashboard') {
        require_once __DIR__ . '/dashboard.php';
    }
    // Rotas de Template
    elseif ($endpoint === 'template') {
        require_once __DIR__ . '/template.php';
    }
    else {
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint não encontrado']);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
?>