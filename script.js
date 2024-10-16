const AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";

// Função para carregar chaves do JSON
async function loadKeys() {
    const response = await fetch('keys.json');
    return response.json();
}

// Função para salvar chaves no JSON
async function saveKey(key) {
    let keys = await loadKeys();
    keys.push(key);
    const updatedKeys = JSON.stringify(keys, null, 2);

    // Simula a escrita no arquivo JSON (em um ambiente real, isso precisa de um backend)
    console.log("Chaves Atualizadas:", updatedKeys);
}

// Simulação de roteamento baseado na entrada do usuário
function handleRouting() {
    const chave = document.getElementById('keyInput').value.trim();
    const route = chave.split('/')[0]; // Exemplo: "a"
    const key = chave.split('/')[1]; // Exemplo: "chave"

    switch (route) {
        case 'a':
            handleARoute(key);
            break;
        case 'v':
            handleVRoute(key);
            break;
        default:
            document.getElementById('output').innerHTML = "❌ | Método inválido.";
            break;
    }
}

// Rota /a/{chave} - Gera chave criptografada e salva
async function handleARoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida.";
        return;
    }

    const key = generateKey();
    const timestamp = new Date().toLocaleString();

    // Salva a chave no JSON
    await saveKey(key);

    document.getElementById('output').innerHTML = `✅ | Chave gerada com sucesso: ${key} <${timestamp}>`;
}

// Rota /v/{chave} - Lista chaves geradas
async function handleVRoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida.";
        return;
    }

    const keys = await loadKeys();

    if (keys.length === 0) {
        document.getElementById('output').innerHTML = "Nenhuma chave encontrada.";
    } else {
        document.getElementById('output').innerHTML = keys.join('<br>');  // Exibe as chaves
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

    const key = generateKey();
    localStorage.setItem(`${key}.txt`, key);  // Simula arquivo .txt

    const txtKeys = Object.keys(localStorage).filter(key => key.endsWith('.txt'));

    document.getElementById('output').innerHTML = txtKeys.map(key => key.replace('.txt', '')).join('<br>');  // Lista sem a extensão
}

// Rota /d/{key}/{chave} - Deleta chave
function handleDRoute(key, chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Invalid KeyChain[1]";
        return;
    }

    if (localStorage.getItem(key) !== null) {
        localStorage.removeItem(key);
        document.getElementById('output').innerHTML = `✅ | CHAVE ${key} DELETADA COM SUCESSO`;
    } else {
        document.getElementById('output').innerHTML = "❌ | Not Found KeyChain[1]";
    }
}

// Função para gerar uma chave aleatória (com letras maiúsculas e números)
function generateKey() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let key = '';
    for (let i = 0; i < 64; i++) {  // Gera uma chave de 64 caracteres
        key += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return key;
}


