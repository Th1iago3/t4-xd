// Configuração do Firebase (use os dados gerados para o seu projeto)
const firebaseConfig = {
    apiKey: "AIzaSyBPidWKOtA9hfa83A9b11WJBm27NPBTsSo",
    authDomain: "t4-cxd.firebaseapp.com",
    databaseURL: "https://t4-cxd-default-rtdb.firebaseio.com",
    projectId: "t4-cxd",
    storageBucket: "t4-cxd.appspot.com",
    messagingSenderId: "527743510667",
    appId: "1:527743510667:web:b6a750fe315a424ed48c8e"
};

// Inicializa o Firebase
const app = firebase.initializeApp(firebaseConfig);
const database = firebase.database();

const AUTH_KEY = "rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s";

// Função para gerar uma chave aleatória
function generateKey() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Função para salvar uma chave no Firebase
function saveKeyToFirebase(key) {
    firebase.database().ref('keys/' + key).set({
        key: key,
        timestamp: new Date().toISOString()
    });
}

// Função para listar as chaves do Firebase
function listKeysFromFirebase() {
    firebase.database().ref('keys').once('value', function(snapshot) {
        const keys = snapshot.val();
        let output = '';
        for (let key in keys) {
            output += `${keys[key].key}<br>`;
        }
        document.getElementById('output').innerHTML = output || 'Nenhuma chave encontrada.';
    });
}

// Função para deletar todas as chaves do Firebase
function deleteAllKeysFromFirebase() {
    firebase.database().ref('keys').remove().then(() => {
        document.getElementById('output').innerHTML = '✅ | Todas as chaves foram deletadas.';
    });
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
    const key = parts[1];
    const fullChave = parts[2];

    if (chave !== AUTH_KEY) {
        document.getElementById('output').innerHTML = "❌ | Invalid KeyChain[1]";
        return;
    }

    switch (route) {
        case 'a':
            const newKey = generateKey();
            saveKeyToFirebase(newKey);
            document.getElementById('output').innerHTML = `✅ | CHAVE GERADA COM SUCESSO!! ${newKey}`;
            break;
        case 'v':
            listKeysFromFirebase();
            break;
        case 'd':
            if (key === 'all') {
                deleteAllKeysFromFirebase();
            }
            break;
        default:
            document.getElementById('output').innerHTML = "❌ | Invalid Method[1]";
            break;
    }
}

