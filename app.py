# backend/app.py
import datetime
import io
import json
import os

import dotenv
import face_recognition
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from database import Pessoa, RegistroAcesso, db

# Carregar variáveis de ambiente do arquivo .env
print("🔧 Carregando variáveis do arquivo .env...")
dotenv.load_dotenv()

app = Flask(__name__)
# Definir a pasta base do projeto
basedir = os.path.abspath(os.path.dirname(__file__))
print(f"📁 Diretório base do projeto: {basedir}")

# Configuração do banco de dados via variável de ambiente
database_url = os.environ.get('DATABASE_URL', 'postgresql://mobclassapp:dev-senha@127.0.0.1:5432/database')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
print(f"🗄️  URL do banco de dados: {database_url}")

# Configurar CORS
cors_origins = ["https://192.168.1.103:8443", "https://localhost:8443"]
CORS(app, origins=cors_origins)
print(f"🌐 CORS configurado para origens: {cors_origins}")

print("🔗 Inicializando banco de dados...")
db.init_app(app)

with app.app_context():
    try:
        print("📊 Criando tabelas do banco de dados...")
        db.create_all()
        print("✅ Banco de dados criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()

# Lista para armazenar os encodings e nomes das pessoas conhecidas carregadas do DB
known_face_encodings = []
known_face_names = []

def load_known_faces():
    """Carrega os encodings de rostos conhecidos do banco de dados."""
    print("📥 Carregando rostos conhecidos do banco de dados...")
    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []

    try:
        with app.app_context():
            pessoas = Pessoa.query.all()
            print(f"   Pessoas encontradas no banco: {len(pessoas)}")
            
            for i, pessoa in enumerate(pessoas):
                print(f"   Processando pessoa {i+1}: {pessoa.nome}")
                try:
                    # CORREÇÃO: Lê a coluna 'encodings_json' e converte para lista
                    encodings_for_person = json.loads(pessoa.encodings_json)
                    print(f"   Encodings para {pessoa.nome}: {len(encodings_for_person)}")
                    
                    for j, encoding_list in enumerate(encodings_for_person):
                        known_face_encodings.append(np.array(encoding_list))
                        known_face_names.append(pessoa.nome)
                        print(f"   Encoding {j+1} adicionado para {pessoa.nome}")
                except Exception as person_error:
                    print(f"❌ Erro ao processar pessoa {pessoa.nome}: {person_error}")
                    
        print(f"✅ Total carregado: {len(known_face_names)} rostos conhecidos")
        for i, name in enumerate(set(known_face_names)):
            count = known_face_names.count(name)
            print(f"   {name}: {count} encoding(s)")
            
    except Exception as e:
        print(f"❌ Erro ao carregar faces conhecidas: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()

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
    print("🎯 Endpoint /recognize chamado")
    
    if 'image' not in request.files:
        print("❌ Nenhuma imagem fornecida na requisição")
        return jsonify({"error": "Nenhuma imagem fornecida"}), 400

    file = request.files['image']
    if file.filename == '':
        print("❌ Nenhum arquivo selecionado")
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    print(f"📷 Processando imagem: {file.filename}")
    
    try:
        # Carregar a imagem para um array numpy
        print("🔄 Carregando imagem para array numpy...")
        image = face_recognition.load_image_file(io.BytesIO(file.read()))

        print("🔍 Detectando faces na imagem...")
        face_locations = face_recognition.face_locations(image)
        print(f"   Faces encontradas: {len(face_locations)}")
        
        face_encodings = face_recognition.face_encodings(image, face_locations)
        print(f"   Encodings gerados: {len(face_encodings)}")

        # Obtenha a data e hora atuais
        current_time = datetime.datetime.now()

        # Atualiza a lista de rostos conhecidos antes de cada reconhecimento,
        # para garantir que os registros mais recentes sejam usados.
        print("🔄 Atualizando lista de rostos conhecidos...")
        load_known_faces()

        response_data = []
        
        if not face_encodings:
            # Caso não encontre nenhuma face, cria um registro como "Desconhecido"
            print("⚠️  Nenhuma face detectada na imagem")
            with app.app_context():
                new_log = RegistroAcesso(
                    pessoa_id=None,
                    nome_identificado="Desconhecido",
                    reconhecido=False,
                    data_hora=current_time
                )
                db.session.add(new_log)
                db.session.commit()
                print("📝 Registro 'Desconhecido' salvo no banco")
            
            response_data.append({
                "name": "Desconhecido",
                "recognized": False,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        for i, face_encoding in enumerate(face_encodings):
            print(f"🔍 Analisando face {i+1}/{len(face_encodings)}")
            name = "Desconhecido"
            is_recognized = False
            pessoa_id = None

            if known_face_encodings:
                print(f"   Comparando com {len(known_face_encodings)} faces conhecidas...")
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                print(f"   Melhor match: índice {best_match_index}, distância: {face_distances[best_match_index]:.4f}")

                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    is_recognized = True
                    print(f"✅ Face reconhecida como: {name}")
                    
                    # Tenta encontrar o ID da pessoa no banco de dados
                    with app.app_context():
                        pessoa_identificada = Pessoa.query.filter_by(nome=name).first()
                        if pessoa_identificada:
                            pessoa_id = pessoa_identificada.id
                            print(f"   ID da pessoa no banco: {pessoa_id}")
                else:
                    print("❌ Face não reconhecida")
            else:
                print("⚠️  Nenhuma face conhecida carregada no sistema")
            
            # Cria e salva o novo registro de acesso
            print("📝 Salvando registro de acesso no banco...")
            with app.app_context():
                new_log = RegistroAcesso(
                    pessoa_id=pessoa_id,
                    nome_identificado=name,
                    reconhecido=is_recognized,
                    data_hora=current_time
                )
                db.session.add(new_log)
                try:
                    db.session.commit()
                    print(f"✅ Registro salvo: {name} ({'reconhecido' if is_recognized else 'não reconhecido'})")
                except Exception as db_error:
                    print(f"❌ Erro ao salvar no banco: {db_error}")
                    db.session.rollback()

            response_data.append({
                "name": name,
                "recognized": is_recognized,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        print(f"📤 Retornando resposta com {len(response_data)} resultados")
        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Erro no reconhecimento: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()
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
    print("🚀 Iniciando aplicação Flask...")
    
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        print(f"📁 Diretório instance criado: {app.instance_path}")
    except Exception as e:
        print(f"⚠️  Erro ao criar diretório instance: {e}")
    
    host = os.environ.get('BACKEND_HOST', '0.0.0.0')
    port = int(os.environ.get('BACKEND_PORT', 5000))
    
    print(f"🌐 Configuração do servidor:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: True")
    print(f"   URL completa: http://{host}:{port}")
    
    try:
        print("🎯 Chamando app.run()...")
        app.run(debug=True, host=host, port=port)
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        print(f"   Tipo do erro: {type(e).__name__}")
        import traceback
        traceback.print_exc()
