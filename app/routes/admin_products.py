from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.product import CategoriaProducto, Producto
from app import db
from sqlalchemy import exc # Importar para manejar errores de integridad

# Crear una nueva Blueprint para las funcionalidades de administración de productos y categorías
admin_products_bp = Blueprint('admin_products', __name__, template_folder='../templates/admin')

# Middleware para asegurar que solo los administradores accedan a estas rutas
@admin_products_bp.before_request
@login_required
def require_admin_for_products():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden gestionar productos y categorías.', 'danger')
        return redirect(url_for('auth.dashboard'))

# --- Rutas de Gestión de Categorías de Productos ---

@admin_products_bp.route('/categories')
def manage_categories():
    categories = CategoriaProducto.query.all()
    # Para mostrar el número de productos en cada categoría
    categories_with_product_count = []
    for category in categories:
        categories_with_product_count.append({
            'category': category,
            'num_products': category.productos.count()
        })
    return render_template('manage_categories.html', categories_with_product_count=categories_with_product_count)

@admin_products_bp.route('/categories/create', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion') # Puede ser None

        if not nombre:
            flash('El nombre de la categoría es obligatorio.', 'danger')
            return render_template('category_form.html', category=None, is_edit=False)

        if CategoriaProducto.query.filter_by(nombre=nombre).first():
            flash('Ya existe una categoría con ese nombre.', 'danger')
            return render_template('category_form.html', category=None, is_edit=False)

        try:
            new_category = CategoriaProducto(nombre=nombre, descripcion=descripcion)
            db.session.add(new_category)
            db.session.commit()
            flash('Categoría creada exitosamente.', 'success')
            return redirect(url_for('admin_products.manage_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear categoría: {e}', 'danger')

    return render_template('category_form.html', category=None, is_edit=False)

@admin_products_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = CategoriaProducto.query.get_or_404(category_id)

    if request.method == 'POST':
        new_nombre = request.form['nombre']
        new_descripcion = request.form.get('descripcion')

        if not new_nombre:
            flash('El nombre de la categoría es obligatorio.', 'danger')
            return render_template('category_form.html', category=category, is_edit=True)

        # Verificar duplicados de nombre de categoría (excluyendo la propia categoría que se está editando)
        existing_category = CategoriaProducto.query.filter(CategoriaProducto.nombre == new_nombre, CategoriaProducto.id_categoria != category_id).first()
        if existing_category:
            flash('Ya existe otra categoría con ese nombre.', 'danger')
            return render_template('category_form.html', category=category, is_edit=True)

        try:
            category.nombre = new_nombre
            category.descripcion = new_descripcion
            db.session.commit()
            flash('Categoría actualizada exitosamente.', 'success')
            return redirect(url_for('admin_products.manage_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar categoría: {e}', 'danger')

    return render_template('category_form.html', category=category, is_edit=True)

@admin_products_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = CategoriaProducto.query.get_or_404(category_id)

    # Verificar si la categoría tiene productos asociados
    if category.productos.count() > 0:
        flash(f'No se puede eliminar la categoría "{category.nombre}" porque tiene productos asociados. Reasigna o elimina los productos primero.', 'danger')
        return redirect(url_for('admin_products.manage_categories'))

    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Categoría "{category.nombre}" eliminada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar categoría: {e}', 'danger')

    return redirect(url_for('admin_products.manage_categories'))

# --- Rutas de Gestión de Productos ---

@admin_products_bp.route('/products')
def manage_products():
    products = Producto.query.all()
    return render_template('manage_products.html', products=products)

@admin_products_bp.route('/products/create', methods=['GET', 'POST'])
def create_product():
    categories = CategoriaProducto.query.all()
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion')
        costo_compra = request.form['costo_compra']
        precio_venta = request.form['precio_venta']
        id_categoria = request.form['id_categoria']

        # Validaciones básicas
        if not nombre or not costo_compra or not precio_venta or not id_categoria:
            flash('Nombre, costo de compra, precio de venta y categoría son obligatorios.', 'danger')
            return render_template('product_form.html', product=None, is_edit=False, categories=categories)
        
        # Validación de valores numéricos
        try:
            costo_compra = float(costo_compra)
            precio_venta = float(precio_venta)
        except ValueError:
            flash('Costo de compra y precio de venta deben ser números válidos.', 'danger')
            return render_template('product_form.html', product=None, is_edit=False, categories=categories)
        
        if costo_compra <= 0 or precio_venta <= 0:
            flash('Costo de compra y precio de venta deben ser valores positivos.', 'danger')
            return render_template('product_form.html', product=None, is_edit=False, categories=categories)

        # Verificar si el código ya existe (si se proporciona)
        if codigo and Producto.query.filter_by(codigo=codigo).first():
            flash('Ya existe un producto con ese código.', 'danger')
            return render_template('product_form.html', product=None, is_edit=False, categories=categories)

        try:
            new_product = Producto(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                costo_compra=costo_compra,
                precio_venta=precio_venta,
                id_categoria=id_categoria
            )
            db.session.add(new_product)
            db.session.commit()
            flash('Producto creado exitosamente.', 'success')
            return redirect(url_for('admin_products.manage_products'))
        except exc.IntegrityError:
            db.session.rollback()
            flash('Error de integridad: Asegúrate de que el código no esté duplicado y la categoría exista.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear producto: {e}', 'danger')

    return render_template('product_form.html', product=None, is_edit=False, categories=categories)

@admin_products_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Producto.query.get_or_404(product_id)
    categories = CategoriaProducto.query.all()

    if request.method == 'POST':
        new_codigo = request.form.get('codigo')
        new_nombre = request.form['nombre']
        new_descripcion = request.form.get('descripcion')
        new_costo_compra = request.form['costo_compra']
        new_precio_venta = request.form['precio_venta']
        new_id_categoria = request.form['id_categoria']

        # Validaciones básicas
        if not new_nombre or not new_costo_compra or not new_precio_venta or not new_id_categoria:
            flash('Nombre, costo de compra, precio de venta y categoría son obligatorios.', 'danger')
            return render_template('product_form.html', product=product, is_edit=True, categories=categories)
        
        # Validación de valores numéricos
        try:
            new_costo_compra = float(new_costo_compra)
            new_precio_venta = float(new_precio_venta)
        except ValueError:
            flash('Costo de compra y precio de venta deben ser números válidos.', 'danger')
            return render_template('product_form.html', product=product, is_edit=True, categories=categories)
        
        if new_costo_compra <= 0 or new_precio_venta <= 0:
            flash('Costo de compra y precio de venta deben ser valores positivos.', 'danger')
            return render_template('product_form.html', product=product, is_edit=True, categories=categories)

        # Verificar duplicados de código (excluyendo el propio producto que se está editando)
        if new_codigo:
            existing_product = Producto.query.filter(Producto.codigo == new_codigo, Producto.id_producto != product_id).first()
            if existing_product:
                flash('Ya existe otro producto con ese código.', 'danger')
                return render_template('product_form.html', product=product, is_edit=True, categories=categories)
        
        try:
            product.codigo = new_codigo
            product.nombre = new_nombre
            product.descripcion = new_descripcion
            product.costo_compra = new_costo_compra
            product.precio_venta = new_precio_venta
            product.id_categoria = new_id_categoria
            db.session.commit()
            flash('Producto actualizado exitosamente.', 'success')
            return redirect(url_for('admin_products.manage_products'))
        except exc.IntegrityError:
            db.session.rollback()
            flash('Error de integridad: Asegúrate de que el código no esté duplicado y la categoría exista.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {e}', 'danger')

    return render_template('product_form.html', product=product, is_edit=True, categories=categories)

@admin_products_bp.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Producto.query.get_or_404(product_id)

    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Producto "{product.nombre}" eliminado exitosamente.', 'success')
    except exc.IntegrityError:
        db.session.rollback()
        flash(f'No se puede eliminar el producto "{product.nombre}" porque está asociado a otros registros (ej. pedidos, inventario).', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {e}', 'danger')

    return redirect(url_for('admin_products.manage_products'))