from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config
import pymysql

pymysql.install_as_MySQLdb() # Necesario para Flask-SQLAlchemy con PyMySQL

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Define la ruta para redirigir si no está logueado
login_manager.login_message_category = 'info' # Categoría de mensaje para Flash

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Importar y registrar blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Ruta por defecto para redirigir al login
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    with app.app_context():
        db.create_all() # Crea las tablas si no existen

        # Asegúrate de que los roles existan
        from app.models.user import Role
        if not Role.query.filter_by(nombre_rol='Administrador').first():
            db.session.add(Role(nombre_rol='Administrador'))
            db.session.add(Role(nombre_rol='Cajero'))
            db.session.add(Role(nombre_rol='Mesero'))
            db.session.commit()

        # Asegúrate de que un admin exista (con contraseña hasheada)
        from app.models.user import User
        from werkzeug.security import generate_password_hash
        admin_role = Role.query.filter_by(nombre_rol='Administrador').first()
        if admin_role and not User.query.filter_by(nombre_usuario='admin').first():
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256') # Hashing más seguro
            admin_user = User(nombre_usuario='admin', contrasena=hashed_password, nombre_completo='Admin BARS', id_rol=admin_role.id_rol)
            db.session.add(admin_user)
            db.session.commit()

    return app

from app.models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))