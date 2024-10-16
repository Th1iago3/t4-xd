const AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";

// Simulação de roteamento baseado no hash da URL
window.onload = function () {
    handleRouting();  // Chama a função de roteamento ao carregar a página
    window.onhashchange = handleRouting;  // Atualiza quando o hash muda
};

// Função que interpreta o hash e redireciona para a "rota" correta
function handleRouting() {
    const hash = window.location.hash;  // Exemplo: #/a/{chave}
    const parts = hash.slice(2).split('/');  // Remove o '#/' e divide as partes
    const route = parts[0];
    const chave = parts[1];
    const key = parts[1];
    const fullChave = parts[2];

    switch (route) {
        case 'a':
            handleARoute(chave);
            break;
        case 'v':
            handleVRoute(chave);
            break;
        case 'tm':
            handleTMRoute(chave);
            break;
        case 'd':
            handleDRoute(key, fullChave);
            break;
        default:
            document.getElementById('output').innerHTML = "❌ | Rota!";
            break;
    }
}

// Rota /a/{chave} - Gera chave criptografada e salva
function handleARoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida!";
        return;
    }

    const key = generateKey();
    const timestamp = new Date().toLocaleString();

    // Simula a criação de um arquivo via LocalStorage
    localStorage.setItem(key, '');

    document.getElementById('output').innerHTML = `✅ | CHAVE GERADA COM SUCESSO!! ${key} <${timestamp}>`;
}

// Rota /v/{chave} - Lista chaves geradas
function handleVRoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida!";
        return;
    }

    const keys = Object.keys(localStorage).filter(key => localStorage.getItem(key) === '');

    if (keys.length === 0) {
        document.getElementById('output').innerHTML = "Nenhuma chave encontrada.";
    } else {
        document.getElementById('output').innerHTML = keys.join('<br>');  // Enfileira as chaves
    }
}

// Rota /tm/{chave} - Gera chaves em .txt e lista chaves
function handleTMRoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida!";
        return;
    }

    const key = generateKey();
    localStorage.setItem(`${key}.txt`, key);  // Simula arquivo .txt

    const txtKeys = Object.keys(localStorage).filter(key => key.endsWith('.txt'));

    document.getElementById('output').innerHTML = txtKeys.map(key => key.replace('.txt', '')).join('<br>');  // Lista sem a extensão
}

// Rota /d/{key}/{chave} - Deleta chave
function handleDRoute(key, chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida!";
        return;
    }

    if (localStorage.getItem(key) !== null) {
        localStorage.removeItem(key);
        document.getElementById('output').innerHTML = `✅ | CHAVE ${key} DELETADA COM SUCESSO`;
    } else {
        document.getElementById('output').innerHTML = "❌ | Chave não encontrada";
    }
}

// Função para gerar uma chave aleatória
function generateKey() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

