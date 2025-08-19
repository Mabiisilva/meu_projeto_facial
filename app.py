# backend/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import face_recognition
import numpy as np
import io
import os
import json
from flask_cors import CORS
from database import db, Pessoa, RegistroAcesso
import datetime

app = Flask(__name__)
# Definir a pasta base do projeto
basedir = os.path.abspath(os.path.dirname(__file__))
# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mobclassapp:**@**localhost/database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Banco de dados criado com sucesso!")

# Lista para armazenar os encodings e nomes das pessoas conhecidas carregadas do DB
known_face_encodings = []
known_face_names = []

def load_known_faces():
    """Carrega os encodings de rostos conhecidos do banco de dados."""
    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []

    with app.app_context():
        pessoas = Pessoa.query.all()
        for pessoa in pessoas:
            # CORREÇÃO: Lê a coluna 'encodings_json' e converte para lista
            encodings_for_person = json.loads(pessoa.encodings_json)
            for encoding_list in encodings_for_person:
                known_face_encodings.append(np.array(encoding_list))
                known_face_names.append(pessoa.nome)
    print(f"Carregados {len(known_face_names)} rostos conhecidos do banco de dados.")

@app.before_request
def load_faces_before_first_request():
    """Carrega as faces conhecidas antes de processar a primeira requisição."""
    with app.app_context():
        if not known_face_encodings:
            load_known_faces()

@app.route('/')
def home():
    return "API de Reconhecimento Facial está online!"

@app.route('/recognize', methods=['POST'])
def recognize_face():
    """
    Este endpoint recebe uma imagem, realiza o reconhecimento facial,
    e então salva um registro de acesso na base de dados.
    """
    if 'image' not in request.files:
        return jsonify({"error": "Nenhuma imagem fornecida"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    try:
        # Carregar a imagem para um array numpy
        image = face_recognition.load_image_file(io.BytesIO(file.read()))

        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        # Obtenha a data e hora atuais
        current_time = datetime.datetime.now()

        # Atualiza a lista de rostos conhecidos antes de cada reconhecimento,
        # para garantir que os registros mais recentes sejam usados.
        load_known_faces()

        response_data = []
        
        if not face_encodings:
            # Caso não encontre nenhuma face, cria um registro como "Desconhecido"
            with app.app_context():
                new_log = RegistroAcesso(
                    pessoa_id=None,
                    nome_identificado="Desconhecido",
                    reconhecido=False,
                    data_hora=current_time
                )
                db.session.add(new_log)
                db.session.commit()
            
            response_data.append({
                "name": "Desconhecido",
                "recognized": False,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        for face_encoding in face_encodings:
            name = "Desconhecido"
            is_recognized = False
            pessoa_id = None

            if known_face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    is_recognized = True
                    
                    # Tenta encontrar o ID da pessoa no banco de dados
                    with app.app_context():
                        pessoa_identificada = Pessoa.query.filter_by(nome=name).first()
                        if pessoa_identificada:
                            pessoa_id = pessoa_identificada.id
            
            # Cria e salva o novo registro de acesso
            with app.app_context():
                new_log = RegistroAcesso(
                    pessoa_id=pessoa_id,
                    nome_identificado=name,
                    reconhecido=is_recognized,
                    data_hora=current_time
                )
                db.session.add(new_log)
                db.session.commit()

            response_data.append({
                "name": name,
                "recognized": is_recognized,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Erro no reconhecimento: {e}")
        return jsonify({"error": "Erro no processamento da imagem", "details": str(e)}), 500

@app.route('/list_people', methods=['GET'])
def list_people():
    """Retorna uma lista de todas as pessoas cadastradas no banco de dados."""
    
    with app.app_context():
        # Consulta o banco de dados para obter todas as pessoas
        pessoas = Pessoa.query.all()
        
        # Cria uma lista de dicionários com as informações de cada pessoa
        people_list = []
        for pessoa in pessoas:
            people_list.append({
                "id": pessoa.id,
                "nome": pessoa.nome
            })
            
    # Retorna a lista em formato JSON
    return jsonify(people_list), 200

@app.route('/access_log', methods=['GET'])
def access_log():
    with app.app_context():
        # Adicione esta linha para ver o caminho do arquivo do banco de dados
        print(f"Caminho do banco de dados: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        registros = RegistroAcesso.query.order_by(RegistroAcesso.data_hora.desc()).all()
        
        print(f"Número de registros encontrados: {len(registros)}")

        log_list = []
        for registro in registros:
            log_list.append({
                "id": registro.id,
                "nome_identificado": registro.nome_identificado,
                "reconhecido": registro.reconhecido,
                "timestamp": str(registro.data_hora) 
            })
    return jsonify(log_list), 200

@app.route('/register_person_api', methods=['POST'])
def register_person_api():
    if 'image' not in request.files or 'name' not in request.form:
        return jsonify({"error": "Imagem e nome são necessários"}), 400

    person_name = request.form['name']
    file = request.files['image']

    try:
        image = face_recognition.load_image_file(io.BytesIO(file.read()))
        face_encodings = face_recognition.face_encodings(image)

        if not face_encodings:
            return jsonify({"error": "Nenhuma face encontrada na imagem fornecida"}), 400

        # Para simplicidade, pegamos o primeiro encoding encontrado na imagem
        known_encoding = face_encodings[0]
        encoding_list = known_encoding.tolist()

        with app.app_context():
            pessoa_existente = Pessoa.query.filter_by(nome=person_name).first()
            if pessoa_existente:
                pessoa_existente.encodings_json = json.dumps([encoding_list])
                db.session.commit()
                print("Banco usado pelo reconhecimento:", app.config['SQLALCHEMY_DATABASE_URI'])
                # Recarrega as faces conhecidas para que o servidor as utilize imediatamente
                load_known_faces()
                return jsonify({"message": f"Pessoa '{person_name}' atualizada com sucesso!"}), 200
            else:
                nova_pessoa = Pessoa(nome=person_name, encodings_json=json.dumps([encoding_list]))
                db.session.add(nova_pessoa)
                db.session.commit()
                print("Banco usado pelo reconhecimento:", app.config['SQLALCHEMY_DATABASE_URI'])
                # Recarrega as faces conhecidas
                load_known_faces()
                return jsonify({"message": f"Pessoa '{person_name}' registrada com sucesso!"}), 201
    except Exception as e:
        print(f"Erro no registro: {e}")
        return jsonify({"error": "Erro no registro da pessoa", "details": str(e)}), 500

if __name__ == '__main__':
    # Cria a pasta 'instance' se não existir para o SQLite DB
    os.makedirs(app.instance_path, exist_ok=True)

    # Inicia o servidor
    app.run(debug=True, host='0.0.0.0') # host='0.0.0.0' permite acesso de outras máquinas na rede
    @app.cli.command("create-db")
    def create_db():
        """Creates the database tables."""
        db.create_all()
        print("Banco de dados criado com sucesso!")

    if __name__ == '__main__':
        app.run(debug=True)
