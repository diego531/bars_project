from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.branch import Sede #Asignacion de sede

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

    id_sede = db.Column(db.Integer, db.ForeignKey('Sedes.id_sede'), nullable=True) # Puede ser NULL para administradores globales
     # --- RECUPERACIÓN ---
    pregunta_seguridad = db.Column(db.String(150), nullable=True) # pregunta de seguridad
    respuesta_seguridad = db.Column(db.String(255), nullable=True) # Hash de la respuesta
    
    sede = db.relationship('Sede', backref='usuarios', lazy=True) # relacion con sede


    def set_password(self, password):
        self.contrasena = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.contrasena, password)
      # --- MÉTODOS ---
    def set_security_answer(self, answer):
        # Convertimos a minúsculas para que no importe mayús/minús al recuperar
        self.respuesta_seguridad = generate_password_hash(answer.lower().strip(), method='pbkdf2:sha256')

    def check_security_answer(self, answer):
        if not self.respuesta_seguridad:
            return False
        return check_password_hash(self.respuesta_seguridad, answer.lower().strip())

    def get_id(self):
        return str(self.id_usuario) # Flask-Login requiere que retorne una cadena

    def __repr__(self):
        return f'<User {self.nombre_usuario}>'