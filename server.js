const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Caminho do arquivo JSON
const keysFilePath = path.join(__dirname, 'keys.json');

// Rota para a raiz
app.get('/', (req, res) => {
    res.send('Cannot Get /');
});

// Rota para gerar uma chave
app.get('/a/:key', (req, res) => {
    const key = req.params.key;
    if (key !== 'rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s') {
        return res.status(403).send('Chave inválida.');
    }

    const generatedKey = generateKey(); // Gera uma chave
    saveKey(generatedKey); // Salva a chave no JSON
    res.send(`✅ | CHAVE GERADA COM SUCESSO!! ${generatedKey}`);
});

// Rota para listar chaves
app.get('/v/:key', (req, res) => {
    const key = req.params.key;
    if (key !== 'rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s') {
        return res.status(403).send('Chave inválida.');
    }

    const keys = getKeys(); // Recupera as chaves do JSON
    const keysList = keys.join('\n'); // Formata as chaves como lista
    res.send(keysList); // Retorna as chaves como texto simples
});

// Rota para deletar uma chave específica
app.delete('/d/:key/:chave', (req, res) => {
    const key = req.params.key;
    const chave = req.params.chave;
    if (key !== 'rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s') {
        return res.status(403).send('Chave inválida.');
    }

    const keys = getKeys(); // Recupera as chaves do JSON
    const filteredKeys = keys.filter(existingKey => existingKey !== chave); // Remove a chave específica

    if (filteredKeys.length === keys.length) {
        return res.status(404).send('Chave não encontrada.'); // Se não encontrou a chave
    }

    saveKeys(filteredKeys); // Salva as chaves restantes
    res.send(`✅ | CHAVE ${chave} DELETADA COM SUCESSO.`);
});

// Rota para deletar todas as chaves
app.delete('/d/all/:key', (req, res) => {
    const key = req.params.key;
    if (key !== 'rquA9WPlnVk1f5IcSqe3oZprepkoooEdLeFbiYfowzbvg3kZ9NR6MMzFIskfbb8s') {
        return res.status(403).send('Chave inválida.');
    }

    deleteAllKeys(); // Deleta todas as chaves
    res.send('✅ | Todas as chaves foram deletadas com sucesso.');
});

// Função para gerar uma chave aleatória
function generateKey() {
    const length = 64; // Comprimento da chave
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'; // Conjunto de caracteres permitidos
    let key = '';
    for (let i = 0; i < length; i++) {
        key += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    return key;
}

// Função para salvar uma chave no arquivo JSON
function saveKey(key) {
    let keys = getKeys(); // Obtém as chaves existentes
    keys.push(key); // Adiciona a nova chave
    fs.writeFileSync(keysFilePath, JSON.stringify(keys, null, 2)); // Salva no JSON
}

// Função para salvar todas as chaves no arquivo JSON
function saveKeys(keys) {
    fs.writeFileSync(keysFilePath, JSON.stringify(keys, null, 2)); // Salva no JSON
}

// Função para recuperar as chaves do arquivo JSON
function getKeys() {
    if (!fs.existsSync(keysFilePath)) {
        return []; // Retorna um array vazio se o arquivo não existir
    }
    const data = fs.readFileSync(keysFilePath); // Lê o arquivo
    return JSON.parse(data); // Retorna as chaves como um array
}

// Função para deletar todas as chaves
function deleteAllKeys() {
    fs.writeFileSync(keysFilePath, JSON.stringify([])); // Substitui o conteúdo do arquivo por um array vazio
}

// Inicia o servidor
app.listen(PORT, () => {
    console.log(`Servidor rodando na porta ${PORT}`);
});

