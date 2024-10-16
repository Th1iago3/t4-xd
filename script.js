const AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";

// Simulação de roteamento baseado no URL
window.onload = function () {
    const path = window.location.pathname;
    const parts = path.split('/').filter(Boolean);  // Remove partes vazias

    if (parts.length === 2 && parts[0] === 'a') {
        const chave = parts[1];
        handleARoute(chave);
    } else if (parts.length === 2 && parts[0] === 'v') {
        const chave = parts[1];
        handleVRoute(chave);
    } else if (parts.length === 2 && parts[0] === 'tm') {
        const chave = parts[1];
        handleTMRoute(chave);
    } else if (parts.length === 3 && parts[0] === 'd') {
        const key = parts[1];
        const chave = parts[2];
        handleDRoute(key, chave);
    } else {
        document.body.innerHTML = "❌ | Rota inválida!";
    }
};

// Rota /a/{chave} - Gera chave criptografada e salva
function handleARoute(chave) {
    if (chave !== AUTH_KEY) {
        document.body.innerHTML = "❌ | Chave inválida!";
        return;
    }

    const key = generateKey();
    const timestamp = new Date().toLocaleString();

    // Simula a criação de um arquivo via LocalStorage
    localStorage.setItem(key, '');

    document.body.innerHTML = `✅ | CHAVE GERADA COM SUCESSO!! ${key} <${timestamp}>`;
}

// Rota /v/{chave} - Lista chaves geradas
function handleVRoute(chave) {
    if (chave !== AUTH_KEY) {
        document.body.innerHTML = "❌ | Chave inválida!";
        return;
    }

    const keys = Object.keys(localStorage).filter(key => localStorage.getItem(key) === '');

    if (keys.length === 0) {
        document.body.innerHTML = "Nenhuma chave encontrada.";
    } else {
        document.body.innerHTML = keys.join('<br>');  // Enfileira as chaves
    }
}

// Rota /tm/{chave} - Gera chaves em .txt e lista chaves
function handleTMRoute(chave) {
    if (chave !== AUTH_KEY) {
        document.body.innerHTML = "❌ | Chave inválida!";
        return;
    }

    const key = generateKey();
    localStorage.setItem(`${key}.txt`, key);  // Simula arquivo .txt

    const txtKeys = Object.keys(localStorage).filter(key => key.endsWith('.txt'));

    document.body.innerHTML = txtKeys.map(key => key.replace('.txt', '')).join('<br>');  // Lista sem a extensão
}

// Rota /d/{key}/{chave} - Deleta chave
function handleDRoute(key, chave) {
    if (chave !== AUTH_KEY) {
        document.body.innerHTML = "❌ | Chave inválida!";
        return;
    }

    if (localStorage.getItem(key) !== null) {
        localStorage.removeItem(key);
        document.body.innerHTML = `✅ | CHAVE ${key} DELETADA COM SUCESSO`;
    } else {
        document.body.innerHTML = "❌ | Chave não encontrada";
    }
}

// Função para gerar uma chave aleatória
function generateKey() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}
