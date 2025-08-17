# backend/add_known_faces.py
import json
import face_recognition
import os
import numpy as np
from app import app, db
from database import Pessoa # Importa o modelo Pessoa do seu database.py

# Caminho para a pasta com as fotos das pessoas conhecidas
KNOWN_FACES_DIR = 'known_faces_data'

def add_face_to_db(image_path, person_name):
    print(f"Processando {person_name} de {image_path}...")
    try:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)

        if not face_encodings:
            print(f"AVISO: Nenhuma face encontrada em {image_path} para {person_name}.")
            return False

        # Para simplicidade, pegamos o primeiro encoding encontrado na imagem
        # Se você tiver múltiplas faces por pessoa ou quiser mais robustez, precisaria de lógica extra
        known_encoding = face_encodings[0]

        # Converte o array numpy para uma lista para armazenar como JSON
        encoding_list = known_encoding.tolist()

        with app.app_context():
            # Verifica se a pessoa já existe
            pessoa_existente = Pessoa.query.filter_by(nome=person_name).first()
            if pessoa_existente:
                print(f"Pessoa '{person_name}' já existe no banco de dados. Atualizando encoding.")
                pessoa_existente.encodings_json = json.dumps([encoding_list])
            else:
                nova_pessoa = Pessoa(nome=person_name, encodings_json=json.dumps([encoding_list]))
                db.session.add(nova_pessoa)
            db.session.commit()
            print(f"Pessoa '{person_name}' adicionada/atualizada no banco de dados.")
            return True

    except Exception as e:
        print(f"Erro ao processar {image_path} para {person_name}: {e}")
        return False

if __name__ == '__main__':
    # Certifique-se de que o app.py pode ser importado e as tabelas criadas
    with app.app_context():
        db.create_all() # Cria as tabelas se elas não existirem

    # Percorre as imagens na pasta KNOWN_FACES_DIR
    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(KNOWN_FACES_DIR, filename)
            # O nome da pessoa será o nome do arquivo (sem extensão)
            person_name = os.path.splitext(filename)[0].replace('_', ' ').title()
            add_face_to_db(image_path, person_name)

    print("\nProcessamento de rostos conhecidos concluído.")
    print("Execute 'python app.py' para iniciar o servidor Flask.")