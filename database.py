from flask_sqlalchemy import SQLAlchemy
# Remova a linha "from app import db"
import face_recognition

db = SQLAlchemy()

# Mova suas classes de modelo para cá
class Pessoa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    encodings_json = db.Column(db.Text, nullable=False)
    registros = db.relationship('RegistroAcesso', backref='pessoa', lazy=True)

class RegistroAcesso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pessoa_id = db.Column(db.Integer, db.ForeignKey('pessoa.id'), nullable=True)
    nome_identificado = db.Column(db.String(100), nullable=False)
    reconhecido = db.Column(db.Boolean, nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)