coconst AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";

// Carrega as chaves do arquivo keys.json
async function loadKeys() {
    const response = await fetch('keys.json');
    if (!response.ok) {
        return [];  // Retorna um array vazio se não conseguir carregar
    }
    return response.json();
}

// Salva uma chave no arquivo keys.json
async function saveKey(key) {
    let keys = await loadKeys();
    keys.push(key);
    const updatedKeys = JSON.stringify(keys, null, 2);

    // Aqui estamos simulando a escrita, em um ambiente real precisaria de um backend
    console.log("Chaves Atualizadas:", updatedKeys);
}

// Função que simula o roteamento baseado na URL
window.onload = function () {
    handleRouting();  // Chama a função de roteamento ao carregar a página
    window.onhashchange = handleRouting;  // Atualiza quando o hash muda
};

// Função que interpreta o hash e redireciona para a "rota" correta
async function handleRouting() {
    const hash = window.location.hash;  // Exemplo: #/a/{chave}
    const parts = hash.slice(2).split('/');  // Remove o '#/' e divide as partes
    const route = parts[0];
    const chave = parts[1];
    const key = parts[2];

    switch (route) {
        case 'a':
            await handleARoute(chave);
            break;
        case 'v':
            await handleVRoute(chave);
            break;
        case 'd':
            await handleDRoute(key);
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

    // Salva a chave no arquivo JSON
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

// Rota /d/all/{chave} - Deleta todas as chaves
async function handleDRoute(chave) {
    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Chave inválida.";
        return;
    }

    // Limpa o arquivo JSON
    const emptyKeys = JSON.stringify([]);
    console.log("Chaves deletadas. Novo estado:", emptyKeys);  // Simulação de limpeza
    document.getElementById('output').innerHTML = "✅ | Todas as chaves foram deletadas com sucesso.";
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



