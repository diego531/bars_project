from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config
import pymysql
from dateutil import tz #  tz para zonas horarias

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
     #Registrar el filtro Jinja2 para la conversión de fecha
    LOCAL_TZ = tz.gettz('America/Bogota') #  zona horaria local

    @app.template_filter('to_local_time')
    def to_local_time_filter(utc_dt, fmt='%d/%m/%Y %H:%M'): #  formato como parámetro
        if not utc_dt:
            return ""
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=tz.gettz('UTC'))
        
        local_dt = utc_dt.astimezone(LOCAL_TZ)
        return local_dt.strftime(fmt) # AHORA EL FILTRO DEVUELVE LA CADENA FORMATEADA

    # Importar y registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin_branches import admin_branches_bp # Importar la blueprint de admin_branches
    from app.routes.admin_products import admin_products_bp
    from app.routes.admin_inventory import admin_inventory_bp # Importar la blueprint de inventario
    from app.routes.waiter_orders import waiter_orders_bp # Importar la blueprint de pedidos de meseros
    from app.routes.cashier_routes import cashier_bp # Importar el blueprint del cajero
    from app.routes.admin_reports import admin_reports_bp # Importar el blueprint de reportes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_branches_bp, url_prefix='/admin/branches') # Registrar la blueprint con su propio prefijo
    app.register_blueprint(admin_products_bp, url_prefix='/admin') # Registrar la nueva Blueprint con un prefijo /admin
    app.register_blueprint(admin_inventory_bp, url_prefix='/admin/inventory') # Registrar la blueprint de inventario
    app.register_blueprint(waiter_orders_bp, url_prefix='/waiter/orders') # Registrar la blueprint de meseros
    app.register_blueprint(cashier_bp, url_prefix='/cashier') # Registrar el blueprint del cajero
    app.register_blueprint(admin_reports_bp, url_prefix='/admin') # Registrar el blueprint de reportes
    

    # Ruta por defecto para redirigir al login
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))

    with app.app_context():
        # Importa los nuevos modelos para que db.create_all() los considere
        from app.models.user import Role, User
        from app.models.branch import Sede, Mesa # Importa los modelos de sede y mesa
        from app.models.product import CategoriaProducto, Producto
        from app.models.inventory import Inventario # Importar el modelo de Inventario
        from app.models.order import Pedido, DetallePedido # Importar los modelos de Pedido y DetallePedido
        from app.models.payment import Pago # Importar el modelo Pago

        db.create_all() # Crea las tablas si no existen

        # Asegúrarde que los roles existan
        if not Role.query.filter_by(nombre_rol='Administrador').first():
            db.session.add(Role(nombre_rol='Administrador'))
            db.session.add(Role(nombre_rol='Cajero'))
            db.session.add(Role(nombre_rol='Mesero'))
            db.session.commit()
        # Buscar si el usuario admin ya existe
        admin_user = User.query.filter_by(nombre_usuario='admin').first()
        admin_role = Role.query.filter_by(nombre_rol='Administrador').first()

        # Datos correctos de seguridad
        pregunta_correcta = '¿Cual es el nombre del proyecto?'
        respuesta_correcta = 'bars'  # La respuesta será "bars"

        if admin_role:
            if not admin_user:
                # CASO 1: El admin no existe, lo creamos desde cero
                print(">>> Creando usuario Admin por primera vez...")
                new_admin = User(
                    nombre_usuario='admin',
                    nombre_completo='Administrador Principal',
                    id_rol=admin_role.id_rol,
                    id_sede=None,
                    pregunta_seguridad=pregunta_correcta
                )
                new_admin.set_password('admin123')
                new_admin.set_security_answer(respuesta_correcta) # Python genera el hash aquí
                db.session.add(new_admin)
            else:
                # CASO 2: El admin YA existe, corregimos sus datos
                print(">>> Corrigiendo datos de seguridad del Admin existente...")
                admin_user.pregunta_seguridad = pregunta_correcta # 
                admin_user.set_security_answer(respuesta_correcta) # Regenera el hash válido
                db.session.add(admin_user)
            
            db.session.commit()
            
    return app


from app.models.user import User

@login_manager.user_loader
def load_user(user_id):
    # Carga el usuario y precarga la relación 'sede'
    # Esto evitará el AttributeError al acceder a current_user.sede
    return User.query.options(db.joinedload(User.sede)).get(int(user_id))