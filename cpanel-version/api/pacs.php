<?php
$auth = new Auth();
$db = Database::getInstance();
$input = json_decode(file_get_contents('php://input'), true);

// GET /api/pacs - Listar todos os PACs
if ($method === 'GET' && !$resource) {
    $user = $auth->requireAuth();
    $pacs = $db->fetchAll("SELECT * FROM pacs ORDER BY created_at DESC");
    echo json_encode($pacs);
}

// POST /api/pacs - Criar novo PAC
elseif ($method === 'POST' && !$resource) {
    $user = $auth->requireAuth();
    
    $pacId = 'pac_' . bin2hex(random_bytes(6));
    $stmt = $db->query(
        "INSERT INTO pacs (pac_id, user_id, secretaria, secretario, fiscal, telefone, email, endereco, ano) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            $pacId,
            $user['user_id'],
            $input['secretaria'],
            $input['secretario'],
            $input['fiscal'] ?? '',
            $input['telefone'] ?? '',
            $input['email'] ?? '',
            $input['endereco'] ?? '',
            $input['ano'] ?? '2026'
        ]
    );
    
    $pac = $db->fetchOne("SELECT * FROM pacs WHERE pac_id = ?", [$pacId]);
    echo json_encode($pac);
}

// GET /api/pacs/{id} - Obter PAC
elseif ($method === 'GET' && $resource && !$id) {
    $user = $auth->requireAuth();
    $pac = $db->fetchOne("SELECT * FROM pacs WHERE pac_id = ?", [$resource]);
    
    if (!$pac) {
        http_response_code(404);
        echo json_encode(['error' => 'PAC não encontrado']);
    } else {
        echo json_encode($pac);
    }
}

// PUT /api/pacs/{id} - Atualizar PAC
elseif ($method === 'PUT' && $resource && !$id) {
    $user = $auth->requireAuth();
    $pac = $db->fetchOne("SELECT * FROM pacs WHERE pac_id = ?", [$resource]);
    
    if (!$pac) {
        http_response_code(404);
        echo json_encode(['error' => 'PAC não encontrado']);
        exit;
    }
    
    // Verificar permissão
    if (!$user['is_admin'] && $pac['user_id'] !== $user['user_id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Permissão negada']);
        exit;
    }
    
    $fields = [];
    $values = [];
    foreach (['secretaria', 'secretario', 'fiscal', 'telefone', 'email', 'endereco', 'ano'] as $field) {
        if (isset($input[$field])) {
            $fields[] = "$field = ?";
            $values[] = $input[$field];
        }
    }
    
    if (!empty($fields)) {
        $values[] = $resource;
        $db->query("UPDATE pacs SET " . implode(', ', $fields) . " WHERE pac_id = ?", $values);
    }
    
    $pac = $db->fetchOne("SELECT * FROM pacs WHERE pac_id = ?", [$resource]);
    echo json_encode($pac);
}

// DELETE /api/pacs/{id} - Deletar PAC
elseif ($method === 'DELETE' && $resource && !$id) {
    $user = $auth->requireAuth();
    $pac = $db->fetchOne("SELECT * FROM pacs WHERE pac_id = ?", [$resource]);
    
    if (!$pac) {
        http_response_code(404);
        echo json_encode(['error' => 'PAC não encontrado']);
        exit;
    }
    
    if (!$user['is_admin'] && $pac['user_id'] !== $user['user_id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Permissão negada']);
        exit;
    }
    
    $db->query("DELETE FROM pacs WHERE pac_id = ?", [$resource]);
    echo json_encode(['message' => 'PAC excluído']);
}

// GET /api/pacs/{id}/items - Listar itens
elseif ($method === 'GET' && $resource && $id === 'items') {
    $user = $auth->requireAuth();
    $items = $db->fetchAll("SELECT * FROM pac_items WHERE pac_id = ? ORDER BY created_at", [$resource]);
    echo json_encode($items);
}

// POST /api/pacs/{id}/items - Criar item
elseif ($method === 'POST' && $resource && $id === 'items') {
    $user = $auth->requireAuth();
    $pac = $db->fetchOne("SELECT * FROM pacs WHERE pac_id = ?", [$resource]);
    
    if (!$pac) {
        http_response_code(404);
        echo json_encode(['error' => 'PAC não encontrado']);
        exit;
    }
    
    if (!$user['is_admin'] && $pac['user_id'] !== $user['user_id']) {
        http_response_code(403);
        echo json_encode(['error' => 'Permissão negada']);
        exit;
    }
    
    $itemId = 'item_' . bin2hex(random_bytes(6));
    $valorTotal = $input['quantidade'] * $input['valorUnitario'];
    
    $db->query(
        "INSERT INTO pac_items (item_id, pac_id, tipo, catmat, descricao, unidade, quantidade, valorUnitario, valorTotal, prioridade, justificativa, imagemUrl) 
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            $itemId,
            $resource,
            $input['tipo'],
            $input['catmat'] ?? '',
            $input['descricao'],
            $input['unidade'],
            $input['quantidade'],
            $input['valorUnitario'],
            $valorTotal,
            $input['prioridade'],
            $input['justificativa'] ?? '',
            $input['imagemUrl'] ?? null
        ]
    );
    
    // Recalcular totais
    recalculatePacTotals($db, $resource);
    
    $item = $db->fetchOne("SELECT * FROM pac_items WHERE item_id = ?", [$itemId]);
    echo json_encode($item);
}

else {
    http_response_code(404);
    echo json_encode(['error' => 'Rota não encontrada']);
}

function recalculatePacTotals($db, $pacId) {
    $items = $db->fetchAll("SELECT * FROM pac_items WHERE pac_id = ?", [$pacId]);
    
    $stats = [
        'total' => 0,
        'consumo' => 0, 'consumoQtd' => 0,
        'permanente' => 0, 'permanenteQtd' => 0,
        'servicos' => 0, 'servicosQtd' => 0,
        'obras' => 0, 'obrasQtd' => 0
    ];
    
    foreach ($items as $item) {
        $stats['total'] += $item['valorTotal'];
        
        if ($item['tipo'] === 'Material de Consumo') {
            $stats['consumo'] += $item['valorTotal'];
            $stats['consumoQtd']++;
        } elseif ($item['tipo'] === 'Material Permanente') {
            $stats['permanente'] += $item['valorTotal'];
            $stats['permanenteQtd']++;
        } elseif ($item['tipo'] === 'Serviço') {
            $stats['servicos'] += $item['valorTotal'];
            $stats['servicosQtd']++;
        } elseif ($item['tipo'] === 'Obras') {
            $stats['obras'] += $item['valorTotal'];
            $stats['obrasQtd']++;
        }
    }
    
    $db->query(
        "UPDATE pacs SET total_value = ?, stats_consumo = ?, stats_consumo_qtd = ?, 
         stats_permanente = ?, stats_permanente_qtd = ?, stats_servicos = ?, stats_servicos_qtd = ?, 
         stats_obras = ?, stats_obras_qtd = ? WHERE pac_id = ?",
        [
            $stats['total'],
            $stats['consumo'], $stats['consumoQtd'],
            $stats['permanente'], $stats['permanenteQtd'],
            $stats['servicos'], $stats['servicosQtd'],
            $stats['obras'], $stats['obrasQtd'],
            $pacId
        ]
    );
}
?>