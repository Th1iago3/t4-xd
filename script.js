// script.js
const AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";

// Simulação de roteamento baseado no hash da URL
window.onload = function () {
    handleRouting();
    window.onhashchange = handleRouting;
};

// Função que interpreta o hash e redireciona para a "rota" correta
function handleRouting() {
    const hash = window.location.hash; // Exemplo: #/a/{chave}
    const parts = hash.slice(2).split('/'); // Remove o '#/' e divide as partes
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

// Função para gerar uma chave aleatória e salvar via API
function generateAndSaveKey() {
    const newKey = generateKey();
    fetch('/keys.json', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ key: newKey })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('output').innerHTML = `✅ | CHAVE GERADA COM SUCESSO!! ${data.key}`;
    });
}

// Função para listar as chaves via API
function listKeys() {
    fetch('/keys.json')
    .then(response => response.json())
    .then(data => {
        if (data.length > 0) {
            document.getElementById('output').innerHTML = data.join('<br>');
        } else {
            document.getElementById('output').innerHTML = 'Nenhuma chave encontrada.';
        }
    });
}

// Função para deletar todas as chaves via API
function deleteAllKeys() {
    fetch('/keys.json', {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('output').innerHTML = '✅ | Todas as chaves foram deletadas.';
    });
}

// Função para gerar uma chave aleatória
function generateKey() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}
