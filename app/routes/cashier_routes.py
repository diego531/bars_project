# app/routes/cashier_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.order import Pedido, DetallePedido # Pedido y DetallePedido
from app.models.branch import Mesa #  Mesa
from app.models.payment import Pago #  El modelo Pago
from app.models.user import User # Para current_user.id_usuario y roles
from app.utils.algorithms import calcular_devuelta_optima # Voraz


cashier_bp = Blueprint('cashier', __name__, template_folder='../templates/cashier')

# Puente para asegurar que solo los cajeros (o admins para pruebas) accedan a estas rutas
@cashier_bp.before_request
@login_required
def require_cashier_for_payments():
    if current_user.role.nombre_rol not in ['Cajero', 'Administrador']:
        flash('Acceso denegado. Solo cajeros pueden gestionar pagos.', 'danger')
        return redirect(url_for('auth.dashboard')) # O a otra página


@cashier_bp.route('/')
def cashier_dashboard():
    # Asegúrarse de que current_user tenga una sede asignada si es cajero
    if current_user.role.nombre_rol == 'Cajero' and not current_user.id_sede:
        flash('Tu usuario de cajero no tiene una sede asignada. Contacta al administrador.', 'danger')
        return redirect(url_for('auth.dashboard'))

    # Mostrar mesas ocupadas (con pedidos pendientes de pago) para la sede del cajero
    if current_user.role.nombre_rol == 'Cajero':
        mesas_ocupadas = Mesa.query.filter_by(id_sede=current_user.id_sede, estado='ocupada').all()
    else: # Admin (para pruebas)
        mesas_ocupadas = Mesa.query.filter_by(estado='ocupada').all()

    return render_template('cashier_dashboard.html', mesas_ocupadas=mesas_ocupadas, user=current_user)


@cashier_bp.route('/table/<int:mesa_id>/order_details')
def view_order_for_payment(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)

    # Validar que la mesa esté ocupada (y asociada a la sede del cajero si aplica)
    if mesa.estado != 'ocupada':
        flash(f'La mesa {mesa.id_mesa} no está ocupada o no tiene un pedido activo.', 'warning')
        return redirect(url_for('cashier.cashier_dashboard'))
    
    if current_user.role.nombre_rol == 'Cajero' and mesa.id_sede != current_user.id_sede:
        flash('Acceso denegado. Esta mesa no pertenece a tu sede asignada.', 'danger')
        return redirect(url_for('cashier.cashier_dashboard'))

    # Buscar el pedido ACTIVO (pendiente) para esta mesa
    # Asumimos que solo hay un pedido "activo" por mesa en un momento dado para simplificar
    pedido = Pedido.query.filter_by(id_mesa=mesa.id_mesa).filter(
        Pedido.estado.in_(['pendiente', 'en_preparacion', 'servido']) # Estados donde el pedido está abierto
    ).order_by(Pedido.fecha_creacion.desc()).first() # El más reciente

    if not pedido:
        flash(f'No se encontró un pedido activo para la mesa {mesa.id_mesa}.', 'warning')
        return redirect(url_for('cashier.cashier_dashboard'))

    detalles = DetallePedido.query.filter_by(id_pedido=pedido.id_pedido).all()

    return render_template('view_order_for_payment.html', mesa=mesa, pedido=pedido, detalles=detalles)


@cashier_bp.route('/order/<int:pedido_id>/register_payment', methods=['GET', 'POST'])
def register_payment(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    # Validaciones antes de permitir el pago
    if pedido.estado == 'pagado' or pedido.estado == 'cancelado':
        flash(f'El pedido {pedido.id_pedido} ya ha sido {pedido.estado}. No se puede registrar un nuevo pago.', 'warning')
        return redirect(url_for('cashier.view_order_for_payment', mesa_id=pedido.id_mesa))
    
    if current_user.role.nombre_rol == 'Cajero' and pedido.mesa.id_sede != current_user.id_sede:
        flash('Acceso denegado. Este pedido no pertenece a la sede asignada a tu usuario.', 'danger')
        return redirect(url_for('cashier.cashier_dashboard'))


    if request.method == 'POST':
        metodo_pago = request.form.get('metodo_pago')
        monto_recibido_str = request.form.get('monto_recibido')

        if not metodo_pago:
            flash('Debes seleccionar un método de pago.', 'danger')
            return redirect(url_for('cashier.register_payment', pedido_id=pedido.id_pedido))

        try:
            monto_recibido = float(monto_recibido_str)
            # validar si el monto_recibido es suficiente
            if monto_recibido < float(pedido.total_pedido):
                flash('El monto recibido es menor al total del pedido.', 'warning')
                return redirect(url_for('cashier.register_payment', pedido_id=pedido.id_pedido))
            
            # Crear el registro de pago
            new_pago = Pago(
                monto_pago=pedido.total_pedido, # Registramos el total del pedido como monto pagado
                metodo_pago=metodo_pago,
                id_pedido=pedido.id_pedido,
                id_usuario_cajero=current_user.id_usuario
            )
            db.session.add(new_pago)

            # Actualizar el estado del pedido
            pedido.estado = 'pagado'
            db.session.add(pedido)

            # Liberar la mesa
            mesa = pedido.mesa
            mesa.estado = 'libre'
            db.session.add(mesa)

            db.session.commit()
            flash(f'Pago del pedido {pedido.id_pedido} registrado exitosamente. Mesa {mesa.id_mesa} liberada.', 'success')
            
            # Calcular el cambio 
            cambio = monto_recibido - float(pedido.total_pedido)
#--------------------------------------------------------------------------------------------------------------------------        
           # 3. APLICACIÓN DEL ALGORITMO VORAZ
            desglose_devuelta = {} # Inicia vacío

            # SOLO ejecutamos el algoritmo si es efectivo Y sobra dinero
            if metodo_pago == 'efectivo' and cambio > 0:
                desglose_devuelta = calcular_devuelta_optima(cambio)
            elif metodo_pago != 'efectivo':
                # Si es tarjeta/nequi, aunque hayan digitado de más, el cambio real es 0
                # o simplemente no se entrega físico.
                cambio = 0 
            
            # 4. Enviar respuesta a la plantilla
            return render_template(
                'payment_success.html', 
                pedido=pedido, 
                pago=new_pago, # objeto pago creado
                cambio=cambio, 
                desglose=desglose_devuelta # Pasamos el resultado (o vacío si no fue efectivo)
            )
#-----------------------------------------------------------------------------------------------------------------------------            
        except ValueError:
            flash('El monto recibido debe ser un número válido.', 'danger')
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el pago: {e}', 'danger')

    return render_template('register_payment.html', pedido=pedido, mesa=pedido.mesa)