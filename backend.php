<?php

$file_path = './keys.json';

// Carregar o arquivo de chaves
function loadKeys() {
    global $file_path;
    if (!file_exists($file_path)) {
        file_put_contents($file_path, json_encode([]));
    }
    $json = file_get_contents($file_path);
    return json_decode($json, true);
}

// Salvar as chaves no arquivo
function saveKeys($keys) {
    global $file_path;
    file_put_contents($file_path, json_encode($keys));
}

// Verificar a ação passada na requisição
$action = isset($_GET['action']) ? $_GET['action'] : null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    if ($input['action'] === 'save') {
        // Adicionar nova chave
        $keys = loadKeys();
        $keys[] = $input['key'];
        saveKeys($keys);
        echo json_encode(['status' => 'success']);
    } elseif ($input['action'] === 'delete') {
        // Deletar todas as chaves
        saveKeys([]);
        echo json_encode(['status' => 'success']);
    }
} elseif ($action === 'list') {
    // Listar as chaves
    $keys = loadKeys();
    echo json_encode(['keys' => $keys]);
} else {
    echo json_encode(['status' => 'error', 'message' => 'Invalid action']);
}
?>
