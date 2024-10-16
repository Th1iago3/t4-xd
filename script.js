const AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";
const STORAGE_KEY = 'keys_storage';  // Nome da chave usada no LocalStorage

// Função para carregar as chaves do LocalStorage
function loadKeys() {
    const storedKeys = localStorage.getItem(STORAGE_KEY);
    return storedKeys ? JSON.parse(storedKeys) : [];
}

// Função para salvar uma chave no LocalStorage
function saveKey(key) {
    const keys = loadKeys();  // Carrega as chaves existentes
    keys.push(key);  // Adiciona a nova chave
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));  // Salva no LocalStorage
}

// Função para deletar todas as chaves
function deleteAllKeys() {
    localStorage.removeItem(STORAGE_KEY);  // Remove todas as chaves do LocalStorage
}

// Simulação de roteamento baseado no hash da URL
window.onload = function () {
    handleRouting();  // Chama a função de roteamento ao carregar a página
    window.onhashchange = handleRouting;  // Atualiza quando o hash muda
};

// Função que interpreta o hash e redireciona para a "rota" correta
function handleRouting() {
    const hash = window.location.hash;  // Exemplo: #/a/{chave}
    const parts = hash.slice(2).split('/');  // Remove o '#/' e divide as partes
    const route = parts[0];  // Obtém a rota (a, v, d)
    const chave = parts[1];  // Obtém a chave de autorização
    const keyToDelete = parts[2];  // Obtém a chave a ser deletada, se necessário

    switch (route) {
        case 'a':
            handleARoute(chave);
            break;
        case 'v':
            handleVRoute(chave);
            break;
        case 'd':
            handleDRoute(chave, keyToDelete);
            break;
        default:
            document.getElementById('output').innerHTML = "❌ | Método inválido.";
            break;
    }
}

// Rota /a/{chave} - Gera chave criptografada e salva
function handleARoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida.";
        return;
    }

    const key = generateKey();
    const timestamp = new Date().toLocaleString();

    // Salva a chave no LocalStorage
    saveKey(key);

    document.getElementById('output').innerHTML = `✅ | Chave gerada com sucesso: ${key} <${timestamp}>`;
}

// Rota /v/{chave} - Lista chaves geradas
function handleVRoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida.";
        return;
    }

    const storedKeys = loadKeys();  // Carrega as chaves do LocalStorage

    if (storedKeys.length === 0) {
        document.getElementById('output').innerHTML = "Nenhuma chave encontrada.";
    } else {
        document.getElementById('output').innerHTML = storedKeys.join('<br>');  // Exibe as chaves
    }
}

// Rota /d/all/{chave} - Deleta todas as chaves
function handleDRoute(chave, keyToDelete) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida.";
        return;
    }

    if (keyToDelete === 'all') {
        // Deleta todas as chaves do LocalStorage
        deleteAllKeys();
        document.getElementById('output').innerHTML = "✅ | Todas as chaves foram deletadas com sucesso.";
    } else {
        document.getElementById('output').innerHTML = "❌ | Rota inválida para deletar.";
    }
}

// Função para gerar uma chave aleatória
function generateKey() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let key = '';
    for (let i = 0; i < 64; i++) {  // Gera uma chave de 64 caracteres
        key += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return key;
}


