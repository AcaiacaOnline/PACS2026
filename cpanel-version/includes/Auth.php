<?php
require_once 'JWT.php';

class Auth {
    private $db;
    
    public function __construct() {
        $this->db = Database::getInstance()->getConnection();
    }
    
    public function register($email, $password, $name) {
        // Verificar se email já existe
        $stmt = $this->db->prepare("SELECT id FROM users WHERE email = ?");
        $stmt->execute([$email]);
        if ($stmt->fetch()) {
            return ['error' => 'Email já cadastrado'];
        }
        
        $passwordHash = password_hash($password, PASSWORD_BCRYPT);
        $userId = $this->generateUserId();
        
        $stmt = $this->db->prepare(
            "INSERT INTO users (user_id, email, name, password_hash, is_admin, is_active, created_at) 
             VALUES (?, ?, ?, ?, 0, 1, NOW())"
        );
        
        if ($stmt->execute([$userId, $email, $name, $passwordHash])) {
            return $this->getUserByEmail($email);
        }
        
        return ['error' => 'Erro ao criar usuário'];
    }
    
    public function login($email, $password) {
        $user = $this->getUserByEmail($email);
        
        if (!$user || !password_verify($password, $user['password_hash'])) {
            return ['error' => 'Credenciais inválidas'];
        }
        
        if (!$user['is_active']) {
            return ['error' => 'Usuário inativo'];
        }
        
        unset($user['password_hash']);
        $token = JWT::encode(['user_id' => $user['user_id']], JWT_SECRET, JWT_EXPIRATION);
        
        return [
            'token' => $token,
            'user' => $user
        ];
    }
    
    public function getCurrentUser() {
        $token = $this->getTokenFromRequest();
        
        if (!$token) {
            return null;
        }
        
        try {
            $payload = JWT::decode($token, JWT_SECRET);
            return $this->getUserById($payload['user_id']);
        } catch (Exception $e) {
            return null;
        }
    }
    
    public function requireAuth() {
        $user = $this->getCurrentUser();
        if (!$user) {
            http_response_code(401);
            die(json_encode(['error' => 'Não autenticado']));
        }
        return $user;
    }
    
    public function requireAdmin() {
        $user = $this->requireAuth();
        if (!$user['is_admin']) {
            http_response_code(403);
            die(json_encode(['error' => 'Acesso negado']));
        }
        return $user;
    }
    
    private function getUserByEmail($email) {
        $stmt = $this->db->prepare("SELECT * FROM users WHERE email = ?");
        $stmt->execute([$email]);
        return $stmt->fetch();
    }
    
    private function getUserById($userId) {
        $stmt = $this->db->prepare("SELECT id, user_id, email, name, is_admin, is_active, picture, created_at FROM users WHERE user_id = ?");
        $stmt->execute([$userId]);
        return $stmt->fetch();
    }
    
    private function getTokenFromRequest() {
        $headers = getallheaders();
        
        if (isset($headers['Authorization'])) {
            $auth = $headers['Authorization'];
            if (preg_match('/Bearer\s+(\S+)/', $auth, $matches)) {
                return $matches[1];
            }
        }
        
        return $_COOKIE['session_token'] ?? null;
    }
    
    private function generateUserId() {
        return 'user_' . bin2hex(random_bytes(6));
    }
}
?>