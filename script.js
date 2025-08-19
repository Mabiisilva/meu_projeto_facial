// script.js

// 1. Evento de Registro de Pessoa
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const form = e.target; // A variável 'form' já está aqui
    const name = form.querySelector('#person-name').value;
    const image = form.querySelector('#person-image').files[0];
    const statusDiv = document.getElementById('register-status');

    if (!name || !image) {
        statusDiv.innerHTML = '<span class="error">Nome e imagem são necessários.</span>';
        return;
    }

    const formData = new FormData();
    formData.append('name', name);
    formData.append('image', image);

    try {
        const response = await fetch('http://127.0.0.1:5000/register_person_api', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            statusDiv.innerHTML = `<span class="success">${data.message}</span>`;
            // Limpa os campos do formulário
            form.reset();
            // Recarrega as listas após o registro
            listPeople();
        } else {
            statusDiv.innerHTML = `<span class="error">Erro: ${data.error || 'Ocorreu um erro desconhecido.'}</span>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<span class="error">Erro de conexão: Não foi possível alcançar a API.</span>`;
        console.error('Erro:', error);
    }
});

// 2. Evento de Reconhecimento Facial
// script.js

// Elementos da página
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureBtn = document.getElementById('capture-btn');
const recognizeStatusDiv = document.getElementById('recognize-status');
const recognizeForm = document.getElementById('recognize-form'); // Adiciona a referência ao formulário antigo

// Variável para armazenar o stream da câmera
let stream;

// 1. Inicia a câmera
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
    } catch (error) {
        console.error("Erro ao acessar a câmera: ", error);
        recognizeStatusDiv.innerHTML = '<span class="error">Erro: Não foi possível acessar a câmera. Verifique as permissões.</span>';
    }
}

// 2. Evento de Captura de Imagem e Reconhecimento
captureBtn.addEventListener('click', async () => {
    // Desenha o frame do vídeo no canvas
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Converte a imagem do canvas para um arquivo blob
    canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('image', blob, 'webcam.png');

        try {
            const response = await fetch('http://127.0.0.1:5000/recognize', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                const resultHtml = data.map(result =>
                    `<p class="${result.recognized ? 'success' : 'error'}">
                        ${result.name} - ${result.timestamp}
                    </p>`
                ).join('');
                recognizeStatusDiv.innerHTML = resultHtml;
                listAccessLog(); // Recarrega o log de acessos
            } else {
                recognizeStatusDiv.innerHTML = `<span class="error">Erro: ${data.error || 'Ocorreu um erro desconhecido.'}</span>`;
            }
        } catch (error) {
            recognizeStatusDiv.innerHTML = `<span class="error">Erro de conexão: Não foi possível alcançar a API.</span>`;
            console.error('Erro:', error);
        }
    }, 'image/png');
});

// Remove o evento de submit do formulário antigo
if (recognizeForm) {
    recognizeForm.removeEventListener('submit', (e) => e.preventDefault());
}

// Inicia a câmera quando a página carrega
window.addEventListener('load', startCamera);

// Adicione aqui a função listAccessLog e o resto do seu código
// (listPeople, eventos de registro, etc.)


// 3. Função para Listar Pessoas Cadastradas
document.getElementById('list-people-btn').addEventListener('click', listPeople);

async function listPeople() {
    const list = document.getElementById('people-list');
    list.innerHTML = ''; // Limpa a lista antes de carregar

    try {
        const response = await fetch('http://127.0.0.1:5000/list_people');
        const data = await response.json();

        if (response.ok) {
            if (data.length > 0) {
                data.forEach(person => {
                    const li = document.createElement('li');
                    li.textContent = `ID: ${person.id}, Nome: ${person.nome}`;
                    list.appendChild(li);
                });
            } else {
                list.innerHTML = '<li>Nenhuma pessoa cadastrada.</li>';
            }
        } else {
            list.innerHTML = `<li class="error">Erro ao carregar a lista de pessoas.</li>`;
        }
    } catch (error) {
        list.innerHTML = `<li class="error">Erro de conexão: Não foi possível alcançar a API.</li>`;
        console.error('Erro:', error);
    }
}

// 4. Função para Listar o Log de Acessos
document.getElementById('list-log-btn').addEventListener('click', listAccessLog);

async function listAccessLog() {
    const list = document.getElementById('log-list');
    list.innerHTML = ''; // Limpa a lista antes de carregar

    try {
        const response = await fetch('http://127.0.0.1:5000/access_log');
        const data = await response.json();

        if (response.ok) {
            if (data.length > 0) {
                data.forEach(log => {
                    const li = document.createElement('li');
                    li.className = log.reconhecido ? 'success' : 'error';
                    li.textContent = `${log.nome_identificado} - ${log.timestamp} - ${log.reconhecido ? 'Reconhecido' : 'Desconhecido'}`;
                    list.appendChild(li);
                });
            } else {
                list.innerHTML = '<li>Nenhum registro de acesso encontrado.</li>';
            }
        } else {
            list.innerHTML = `<li class="error">Erro ao carregar o log de acessos.</li>`;
        }
    } catch (error) {
        list.innerHTML = `<li class="error">Erro de conexão: Não foi possível alcançar a API.</li>`;
        console.error('Erro:', error);
    }
}