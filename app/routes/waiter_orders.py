# app/routes/waiter_orders.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.order import Pedido, DetallePedido
from app.models.branch import Sede, Mesa
from app.models.product import Producto
from app.models.inventory import Inventario
from app.models.user import User # Asegurarse de tener el modelo User para current_user.id_usuario

waiter_orders_bp = Blueprint('waiter_orders', __name__, template_folder='../templates/waiter')

# Middleware para asegurar que solo los meseros (o admins por ahora) accedan a estas rutas
@waiter_orders_bp.before_request
@login_required
def require_waiter_for_orders():
    if current_user.role.nombre_rol not in ['Mesero', 'Administrador']:
        flash('Acceso denegado. Solo meseros pueden gestionar pedidos.', 'danger')
        # Redirigir a un dashboard genérico o de login si no es un mesero/admin
        return redirect(url_for('auth.dashboard')) 

# --- Rutas para la aplicación web móvil del Mesero ---

# Página principal del mesero para ver sus mesas y pedidos
@waiter_orders_bp.route('/')
def waiter_dashboard():
    # Inicializa las listas vacías
    mesas_disponibles = []
    pedidos_abiertos = []
    
    # Validar que el mesero tenga una sede asignada
    if current_user.role.nombre_rol == 'Mesero':
        if not current_user.id_sede:
            flash('Tu usuario de mesero no tiene una sede asignada. Contacta al administrador.', 'danger')
            # Las listas quedan vacías, el template mostrará "No hay mesas/pedidos"
        else:
            # Filtra mesas por la sede del mesero actual y estado 'libre'
            mesas_disponibles = Mesa.query.filter_by(id_sede=current_user.id_sede, estado='libre').all()
            
            # Pedidos abiertos del mesero actual, asociados a su sede (es una buena práctica)
            # Aunque la consulta de Pedido ya filtra por id_usuario_mesero, lo cual ya implica la sede
            pedidos_abiertos = Pedido.query.filter_by(id_usuario_mesero=current_user.id_usuario, estado='pendiente').all()
    elif current_user.role.nombre_rol == 'Administrador':
        # Para administradores que acceden a este dashboard (para pruebas, por ejemplo)
        # Podrías mostrar todas las mesas libres o pedirles que seleccionen una sede
        mesas_disponibles = Mesa.query.filter_by(estado='libre').all()
        pedidos_abiertos = Pedido.query.filter_by(estado='pendiente').all() # O filtrar por algún admin si tuviera pedidos
    
    # Renderiza la plantilla y pasa todas las variables necesarias
    return render_template(
        'waiter_dashboard.html',
        user=current_user,
        mesas_disponibles=mesas_disponibles,
        pedidos_abiertos=pedidos_abiertos
    )


@waiter_orders_bp.route('/create_order/<int:mesa_id>', methods=['GET', 'POST'])
def create_order(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    
    # Validar que la mesa esté libre
    if mesa.estado != 'libre':
        flash(f'La mesa {mesa.id_mesa} ya está ocupada o tiene un pedido abierto. No se puede crear un nuevo pedido.', 'danger')
        return redirect(url_for('waiter_orders.waiter_dashboard'))

    # Productos disponibles en el inventario de la sede de la mesa
    # Filtramos por productos que no estén bloqueados y con cantidad > 0
    productos_en_inventario = Inventario.query.filter_by(id_sede=mesa.id_sede, esta_bloqueado=False).filter(Inventario.cantidad > 0).all()
    
    if request.method == 'POST':
        # Crear el pedido
        new_pedido = Pedido(
            estado='pendiente',
            total_pedido=0.00, # Se actualizará al añadir productos
            id_usuario_mesero=current_user.id_usuario,
            id_mesa=mesa.id_mesa
        )
        db.session.add(new_pedido)
        
        # Ocupar la mesa
        mesa.estado = 'ocupada'
        db.session.add(mesa) # Añadir la mesa modificada a la sesión

        try:
            db.session.commit()
            flash(f'Pedido para la mesa {mesa.id_mesa} creado exitosamente. Ahora puedes añadir productos.', 'success')
            return redirect(url_for('waiter_orders.add_products_to_order', pedido_id=new_pedido.id_pedido))
        except Exception as e:
            db.session.rollback()
            mesa.estado = 'libre' # Revertir estado de la mesa si falla la creación del pedido
            flash(f'Error al crear el pedido: {e}', 'danger')
            return redirect(url_for('waiter_orders.waiter_dashboard'))
    
    # Si es GET, simplemente mostramos el formulario para crear el pedido (que en este caso es más una confirmación)
    return render_template('create_order.html', mesa=mesa, productos_en_inventario=productos_en_inventario)


@waiter_orders_bp.route('/order/<int:pedido_id>/add_products', methods=['GET', 'POST'])
def add_products_to_order(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    # Solo se pueden añadir productos a pedidos "pendientes" (o "en_preparacion" si se definiera ese estado)
    if pedido.estado not in ['pendiente', 'en_preparacion']:
        flash(f'No se pueden añadir productos a un pedido en estado "{pedido.estado}".', 'danger')
        return redirect(url_for('waiter_orders.view_order_details', pedido_id=pedido.id_pedido))
    
    # Productos disponibles en el inventario de la sede de la mesa del pedido
    # Filtramos por productos que no estén bloqueados y con cantidad > 0
    # Obtenemos solo los productos, no los objetos Inventario directamente para el select
    productos_disponibles_inv = Inventario.query.filter_by(id_sede=pedido.mesa.id_sede, esta_bloqueado=False).filter(Inventario.cantidad > 0).all()
    productos_para_seleccion = []
    for inv_item in productos_disponibles_inv:
        productos_para_seleccion.append(inv_item.producto) # Añadir el objeto Producto

    if request.method == 'POST':
        id_producto = request.form.get('id_producto', type=int)
        cantidad_solicitada = request.form.get('cantidad', type=int)

        if not id_producto or not cantidad_solicitada or cantidad_solicitada <= 0:
            flash('Debes seleccionar un producto y especificar una cantidad válida.', 'danger')
            return render_template('add_products_to_order.html', pedido=pedido, productos_para_seleccion=productos_para_seleccion)

        # Buscar el inventario del producto en la sede de la mesa
        inventario_item = Inventario.query.filter_by(
            id_producto=id_producto,
            id_sede=pedido.mesa.id_sede
        ).first()

        if not inventario_item or inventario_item.esta_bloqueado or inventario_item.cantidad < cantidad_solicitada:
            flash(f'No hay suficiente stock disponible para el producto seleccionado o está bloqueado. Stock actual: {inventario_item.cantidad if inventario_item else 0}', 'danger')
            return render_template('add_products_to_order.html', pedido=pedido, productos_para_seleccion=productos_para_seleccion)

        # Obtener el producto para sus precios
        producto = Producto.query.get(id_producto)
        if not producto:
            flash('Producto no encontrado.', 'danger')
            return render_template('add_products_to_order.html', pedido=pedido, productos_para_seleccion=productos_para_seleccion)

        try:
            # Crear o actualizar DetallePedido
            detalle = DetallePedido.query.filter_by(id_pedido=pedido.id_pedido, id_producto=id_producto).first()
            if detalle:
                # Si el producto ya está en el pedido, actualizar cantidad y subtotal
                detalle.cantidad += cantidad_solicitada
                detalle.subtotal = detalle.cantidad * detalle.precio_unitario
                db.session.add(detalle)
            else:
                # Si es un nuevo producto en el pedido, crear un nuevo DetallePedido
                subtotal = cantidad_solicitada * producto.precio_venta
                new_detalle = DetallePedido(
                    cantidad=cantidad_solicitada,
                    precio_unitario=producto.precio_venta,
                    costo_unitario=producto.costo_compra,
                    subtotal=subtotal,
                    id_pedido=pedido.id_pedido,
                    id_producto=id_producto
                )
                db.session.add(new_detalle)
            
            # Actualizar el total del pedido
            pedido.total_pedido += (cantidad_solicitada * producto.precio_venta)
            db.session.add(pedido)

            # Reducir la cantidad en el inventario
            inventario_item.cantidad -= cantidad_solicitada
            if inventario_item.cantidad == 0:
                inventario_item.esta_bloqueado = True # Bloquear si el stock llega a cero
            db.session.add(inventario_item)

            db.session.commit()
            flash('Productos añadidos al pedido exitosamente.', 'success')
            return redirect(url_for('waiter_orders.view_order_details', pedido_id=pedido.id_pedido))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al añadir productos al pedido: {e}', 'danger')

    return render_template('add_products_to_order.html', pedido=pedido, productos_para_seleccion=productos_para_seleccion)


@waiter_orders_bp.route('/order/<int:pedido_id>/details')
def view_order_details(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    # Cargar los detalles del pedido con sus productos
    detalles = DetallePedido.query.filter_by(id_pedido=pedido_id).all()
    return render_template('view_order_details.html', pedido=pedido, detalles=detalles)