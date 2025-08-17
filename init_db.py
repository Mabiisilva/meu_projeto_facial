# backend/init_db.py
from app import app, db
import os

# A pasta 'data' é criada automaticamente pelo Flask, mas podemos garantir aqui
instance_path = os.path.join(app.root_path, 'data')
os.makedirs(instance_path, exist_ok=True) # Garante que a pasta 'data' existe

with app.app_context():
    print("Criando tabelas do banco de dados...")
    db.create_all()
    print("Tabelas criadas com sucesso! O arquivo site.db deve estar na pasta 'data'.")