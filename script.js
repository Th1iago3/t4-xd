const AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";

// Função para fazer requisições ao PHP
function makeRequest(url, method = 'GET', data = null) {
    return fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: data ? JSON.stringify(data) : null
    }).then(response => response.json());
}

// Simulação de roteamento baseado no hash da URL
window.onload = function () {
    handleRouting();
    window.onhashchange = handleRouting;
};

// Função que interpreta o hash e redireciona para a "rota" correta
function handleRouting() {
    const hash = window.location.hash;  // Exemplo: #/a/{chave}
    const parts = hash.slice(2).split('/');  // Remove o '#/' e divide as partes
    const route = parts[0];
    const chave = parts[1];
    const key = parts[2];

    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Invalid KeyChain[1]";
        return;
    }

    switch (route) {
        case 'a':
            generateAndSaveKey();
            break;
        case 'v':
            listKeys();
            break;
        case 'd':
            if (key === 'all') {
                deleteAllKeys();
            }
            break;
        default:
            document.getElementById('output').innerHTML = "❌ | Invalid Method[1]";
            break;
    }
}

// Função para gerar uma chave aleatória e salvar via PHP
function generateAndSaveKey() {
    const newKey = generateKey();
    makeRequest('backend.php', 'POST', { action: 'save', key: newKey })
        .then(response => {
            document.getElementById('output').innerHTML = `✅ | CHAVE GERADA COM SUCESSO!! ${newKey}`;
        });
}

// Função para listar as chaves via PHP
function listKeys() {
    makeRequest('backend.php?action=list')
        .then(response => {
            if (response.keys.length > 0) {
                document.getElementById('output').innerHTML = response.keys.join('<br>');
            } else {
                document.getElementById('output').innerHTML = 'Nenhuma chave encontrada.';
            }
        });
}

// Função para deletar todas as chaves via PHP
function deleteAllKeys() {
    makeRequest('backend.php', 'POST', { action: 'delete' })
        .then(response => {
            document.getElementById('output').innerHTML = '✅ | Todas as chaves foram deletadas.';
        });
}

// Função para gerar uma chave aleatória
function generateKey() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}


