<?php
$auth = new Auth();
$input = json_decode(file_get_contents('php://input'), true);

if ($resource === 'register' && $method === 'POST') {
    if (!isset($input['email']) || !isset($input['password']) || !isset($input['name'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Dados incompletos']);
        exit;
    }
    
    $result = $auth->register($input['email'], $input['password'], $input['name']);
    
    if (isset($result['error'])) {
        http_response_code(400);
    }
    
    echo json_encode($result);
}

elseif ($resource === 'login' && $method === 'POST') {
    if (!isset($input['email']) || !isset($input['password'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Dados incompletos']);
        exit;
    }
    
    $result = $auth->login($input['email'], $input['password']);
    
    if (isset($result['error'])) {
        http_response_code(401);
    } else {
        // Definir cookie
        setcookie('session_token', $result['token'], time() + JWT_EXPIRATION, '/', '', true, true);
    }
    
    echo json_encode($result);
}

elseif ($resource === 'me' && $method === 'GET') {
    $user = $auth->getCurrentUser();
    
    if (!$user) {
        http_response_code(401);
        echo json_encode(['error' => 'Não autenticado']);
    } else {
        echo json_encode($user);
    }
}

elseif ($resource === 'logout' && $method === 'POST') {
    setcookie('session_token', '', time() - 3600, '/', '', true, true);
    echo json_encode(['message' => 'Logout realizado']);
}

else {
    http_response_code(404);
    echo json_encode(['error' => 'Rota não encontrada']);
}
?>