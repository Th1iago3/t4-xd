// server.js
const express = require('express');
const fs = require('fs');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000; // Permite que o Render defina a porta

const FILE_PATH = path.join(__dirname, 'keys.json');

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public')); // Para servir arquivos estáticos do diretório 'public'

// Carregar as chaves do arquivo
function loadKeys() {
    if (!fs.existsSync(FILE_PATH)) {
        fs.writeFileSync(FILE_PATH, JSON.stringify([])); // Cria o arquivo se não existir
    }
    const data = fs.readFileSync(FILE_PATH);
    return JSON.parse(data);
}

// Salvar as chaves no arquivo
function saveKeys(keys) {
    fs.writeFileSync(FILE_PATH, JSON.stringify(keys, null, 2));
}

// Endpoint para acessar o arquivo keys.json
app.get('/keys.json', (req, res) => {
    const keys = loadKeys();
    res.json(keys);
});

// Endpoint para salvar uma nova chave
app.post('/keys.json', (req, res) => {
    const keys = loadKeys();
    keys.push(req.body.key);
    saveKeys(keys);
    res.json({ status: 'success', key: req.body.key });
});

// Endpoint para deletar todas as chaves
app.delete('/keys.json', (req, res) => {
    saveKeys([]); // Salva um array vazio
    res.json({ status: 'success', message: 'Todas as chaves foram deletadas.' });
});

// Iniciar o servidor
app.listen(PORT, () => {
    console.log(`Servidor rodando em http://localhost:${PORT}`);
});
