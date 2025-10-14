from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    __tablename__ = 'Roles'
    id_rol = db.Column(db.Integer, primary_key=True)
    nombre_rol = db.Column(db.String(45), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.nombre_rol}>'

class User(UserMixin, db.Model):
    __tablename__ = 'Usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(45), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False) # Guardará el hash
    nombre_completo = db.Column(db.String(45), nullable=False)
    id_rol = db.Column(db.Integer, db.ForeignKey('Roles.id_rol'), nullable=False)

    def set_password(self, password):
        self.contrasena = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.contrasena, password)

    def get_id(self):
        return str(self.id_usuario) # Flask-Login requiere que retorne una cadena

    def __repr__(self):
        return f'<User {self.nombre_usuario}>'