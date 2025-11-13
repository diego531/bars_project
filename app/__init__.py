from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config
import pymysql

pymysql.install_as_MySQLdb()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # Importar y registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin_branches import admin_branches_bp # NUEVO: Importar la blueprint de admin_branches
    from app.routes.admin_products import admin_products_bp
    from app.routes.admin_inventory import admin_inventory_bp # NUEVO: Importar la blueprint de inventario
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_branches_bp, url_prefix='/admin/branches') # NUEVO: Registrar la blueprint con su propio prefijo
    app.register_blueprint(admin_products_bp, url_prefix='/admin') # NUEVO: Registrar la nueva Blueprint con un prefijo /admin
    app.register_blueprint(admin_inventory_bp, url_prefix='/admin/inventory') # NUEVO: Registrar la blueprint de inventario
    

    # Ruta por defecto para redirigir al login
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    with app.app_context():
        # Importa los nuevos modelos para que db.create_all() los considere
        from app.models.user import Role, User
        from app.models.branch import Sede, Mesa # NUEVO: Importa los modelos de sede y mesa
        from app.models.product import CategoriaProducto, Producto
        from app.models.inventory import Inventario # NUEVO: Importar el modelo de Inventario

        db.create_all() # Crea las tablas si no existen

        # Asegúrate de que los roles existan
        if not Role.query.filter_by(nombre_rol='Administrador').first():
            db.session.add(Role(nombre_rol='Administrador'))
            db.session.add(Role(nombre_rol='Cajero'))
            db.session.add(Role(nombre_rol='Mesero'))
            db.session.commit()

        # Asegúrate de que un admin exista (con contraseña hasheada)
        admin_role = Role.query.filter_by(nombre_rol='Administrador').first()
        if admin_role and not User.query.filter_by(nombre_usuario='admin').first():
            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin_user = User(nombre_usuario='admin', contrasena=hashed_password, nombre_completo='Admin BARS', id_rol=admin_role.id_rol)
            db.session.add(admin_user)
            db.session.commit()

    return app

from app.models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))