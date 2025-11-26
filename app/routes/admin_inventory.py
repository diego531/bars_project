from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.inventory import Inventario # modelo de Inventario
from app.models.product import Producto # Necesario para listar productos disponibles
from app.models.branch import Sede # Necesario para la sede específica
from app import db
from sqlalchemy import exc
from app.utils.algorithms import ordenar_inventario_por_stock, calcular_valor_inventario_recursivo #Recursivo
from app.utils.algorithms import recomendar_reabastecimiento # Mochila

admin_inventory_bp = Blueprint('admin_inventory', __name__, template_folder='../templates/admin')

# Puente para asegurar que solo los administradores accedan a estas rutas
@admin_inventory_bp.before_request
@login_required
def require_admin_for_inventory():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden gestionar el inventario.', 'danger')
        return redirect(url_for('auth.dashboard'))

# --- RUTAS DE GESTIÓN DE INVENTARIO POR SEDE ---
#------------------------------------------------------------------------------------
@admin_inventory_bp.route('/optimize/<int:sede_id>', methods=['GET', 'POST'])
@login_required
def optimize_restock(sede_id):
    sede = Sede.query.get_or_404(sede_id)
    resultado_items = []
    ganancia_maxima = 0
    presupuesto = 0

    if request.method == 'POST':
        presupuesto = request.form.get('presupuesto', type=int)
        
        # Obtenemos productos candidatos (ej: todos los productos del sistema)
        productos = Producto.query.all()
        lista_candidatos = []
        
        for p in productos:
            # Definimos:
            # Costo (Peso en la mochila) = costo_compra
            # Valor (Ganancia en la mochila) = precio_venta - costo_compra
            ganancia = float(p.precio_venta) - float(p.costo_compra)
            
            if ganancia > 0: # Solo consideramos productos rentables
                lista_candidatos.append({
                    'id': p.id_producto,
                    'nombre': p.nombre,
                    'costo': int(p.costo_compra),
                    'ganancia': int(ganancia)
                })
        
        # EJECUTAR ALGORITMO DE LA MOCHILA
        resultado_items, ganancia_maxima = recomendar_reabastecimiento(presupuesto, lista_candidatos)
#-------------------------------------------------------------------------------------------------------

    return render_template('optimize_restock.html', sede=sede, items=resultado_items, ganancia=ganancia_maxima, presupuesto=presupuesto)

@admin_inventory_bp.route('/<int:sede_id>')
def manage_inventory(sede_id):
    sede = Sede.query.get_or_404(sede_id)
    
    # Traemos TODO sin ordenar por SQL
    inventario_query = Inventario.query.filter_by(id_sede=sede_id).all()
#----------------------------------------------------------------------------------------------------
    # 1. ALGORITMO ITERATIVO: Bubble Sort
    # Ordenamos para ver primero los productos con menos stock
    inventario_ordenado = ordenar_inventario_por_stock(inventario_query)
    
    # 2. ALGORITMO RECURSIVO: Valor Total
    valor_total_sede = calcular_valor_inventario_recursivo(inventario_ordenado, len(inventario_ordenado))
    
    # Pasamos 'valor_total_sede' al template para mostrarlo arriba
    return render_template('manage_inventory.html', sede=sede, inventario=inventario_ordenado, valor_total=valor_total_sede)
#----------------------------------------------------------------------------------------------------

@admin_inventory_bp.route('/assign/<int:sede_id>', methods=['GET', 'POST'])
def assign_product_to_branch(sede_id):
    sede = Sede.query.get_or_404(sede_id)
    
    # Obtener los IDs de los productos ya asignados a esta sede
    productos_en_sede_ids = [item.id_producto for item in Inventario.query.filter_by(id_sede=sede_id).all()]
    # Obtener todos los productos que AÚN NO están asignados a esta sede
    productos_disponibles = Producto.query.filter(Producto.id_producto.notin_(productos_en_sede_ids)).all()

    if request.method == 'POST':
        id_producto = request.form.get('id_producto', type=int)
        cantidad = request.form.get('cantidad', type=int)
        esta_bloqueado = 'esta_bloqueado' in request.form # Coge el valor si el checkbox está marcado

        if not id_producto:
            flash('Debes seleccionar un producto.', 'danger')
            return render_template('assign_product_to_branch.html', sede=sede, productos_disponibles=productos_disponibles)

        if cantidad is None or cantidad < 0:
            flash('La cantidad debe ser un número positivo o cero.', 'danger')
            return render_template('assign_product_to_branch.html', sede=sede, productos_disponibles=productos_disponibles)

        # Si se bloquea explícitamente, la cantidad debería ser 0.
        if esta_bloqueado:
            cantidad = 0

        try:
            new_inventory_item = Inventario(
                cantidad=cantidad,
                esta_bloqueado=esta_bloqueado,
                id_producto=id_producto,
                id_sede=sede_id
            )
            db.session.add(new_inventory_item)
            db.session.commit()
            flash('Producto asignado al inventario de la sede exitosamente.', 'success')
            return redirect(url_for('admin_inventory.manage_inventory', sede_id=sede_id))
        except exc.IntegrityError:
            db.session.rollback()
            flash('Error de integridad: El producto ya podría estar asignado a esta sede.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al asignar producto al inventario: {e}', 'danger')

    return render_template('assign_product_to_branch.html', sede=sede, productos_disponibles=productos_disponibles)


@admin_inventory_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_inventory_item(item_id):
    inventory_item = Inventario.query.get_or_404(item_id)
    sede = Sede.query.get_or_404(inventory_item.id_sede)
    producto = Producto.query.get_or_404(inventory_item.id_producto)

    if request.method == 'POST':
        new_cantidad = request.form.get('cantidad', type=int)
        new_esta_bloqueado = 'esta_bloqueado' in request.form

        if new_cantidad is None or new_cantidad < 0:
            flash('La cantidad debe ser un número positivo o cero.', 'danger')
            return render_template('edit_inventory_item.html', inventory_item=inventory_item, sede=sede, producto=producto)
        
        # Si se marca como bloqueado, la cantidad se fuerza a 0.
        # Si no se marca como bloqueado y la cantidad es 0, también se considera bloqueado lógicamente
        if new_esta_bloqueado or new_cantidad == 0:
            inventory_item.esta_bloqueado = True
            inventory_item.cantidad = 0 # Asegurar que la cantidad sea 0 si está bloqueado
        else:
            inventory_item.esta_bloqueado = False
            inventory_item.cantidad = new_cantidad # Actualizar con la cantidad proporcionada

        try:
            db.session.commit()
            flash('Inventario de producto actualizado exitosamente.', 'success')
            return redirect(url_for('admin_inventory.manage_inventory', sede_id=sede.id_sede))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar inventario: {e}', 'danger')

    return render_template('edit_inventory_item.html', inventory_item=inventory_item, sede=sede, producto=producto)


@admin_inventory_bp.route('/toggle_block/<int:item_id>', methods=['POST'])
def toggle_block_inventory_item(item_id):
    inventory_item = Inventario.query.get_or_404(item_id)
    sede = Sede.query.get_or_404(inventory_item.id_sede)

    try:
        if inventory_item.esta_bloqueado:
            # Si estaba bloqueado, lo desbloqueamos y le ponemos cantidad 1 por defecto (o podrías pedirla)
            inventory_item.esta_bloqueado = False
            inventory_item.cantidad = 1 # O se podría dejar en 0 y esperar una edición explícita.
            flash(f'Producto "{inventory_item.producto.nombre}" desbloqueado en {sede.nombre_sede}.', 'success')
        else:
            # Si no estaba bloqueado, lo bloqueamos y ponemos cantidad a 0
            inventory_item.esta_bloqueado = True
            inventory_item.cantidad = 0
            flash(f'Producto "{inventory_item.producto.nombre}" bloqueado en {sede.nombre_sede} (cantidad ajustada a 0).', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado del inventario: {e}', 'danger')

    return redirect(url_for('admin_inventory.manage_inventory', sede_id=sede.id_sede))


@admin_inventory_bp.route('/remove/<int:item_id>', methods=['POST'])
def remove_inventory_item(item_id):
    inventory_item = Inventario.query.get_or_404(item_id)
    sede_id = inventory_item.id_sede # Guardar la sede_id antes de eliminar

    if inventory_item.cantidad > 0:
        flash(f'No se puede desasignar el producto "{inventory_item.producto.nombre}" de {inventory_item.sede.nombre_sede} porque tiene stock. Bloquéalo primero.', 'danger')
        return redirect(url_for('admin_inventory.manage_inventory', sede_id=sede_id))
    
    # Si la cantidad es 0, procedemos a la eliminación física del registro de inventario.
    try:
        db.session.delete(inventory_item)
        db.session.commit()
        flash(f'Producto "{inventory_item.producto.nombre}" desasignado del inventario de {inventory_item.sede.nombre_sede} exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desasignar producto del inventario: {e}', 'danger')

    return redirect(url_for('admin_inventory.manage_inventory', sede_id=sede_id))