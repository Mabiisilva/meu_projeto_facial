# backend/init_db.py
from app import app, db
import os

# Caminho absoluto da pasta 'data'
data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
os.makedirs(data_path, exist_ok=True)  # Cria se não existir

with app.app_context():
    print("Criando tabelas do banco de dados...")
    db.create_all()
    print(f"Tabelas criadas com sucesso! O arquivo database.db deve estar na pasta '{data_path}'.")