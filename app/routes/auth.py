from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User, Role
from app import db

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard')) # Redirige si ya está logueado

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_id = request.form['role']

        user = User.query.filter_by(nombre_usuario=username, id_rol=role_id).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'¡Bienvenido, {user.nombre_completo}!', 'success')
            # Redirigir según el rol
            if user.role.nombre_rol == 'Administrador':
                return redirect(url_for('auth.admin_dashboard')) # Cambiar a la ruta real de admin
            elif user.role.nombre_rol == 'Cajero':
                return redirect(url_for('auth.cashier_dashboard')) # Cambiar a la ruta real de cajero
            elif user.role.nombre_rol == 'Mesero':
                return redirect(url_for('auth.waiter_dashboard')) # Cambiar a la ruta real de mesero
            return redirect(url_for('auth.dashboard')) # Ruta por defecto si no es ninguno de los anteriores
        else:
            flash('Datos incorrectos. Por favor, verifica tu usuario, contraseña y rol.', 'danger')
            return render_template('login.html', username=username, selected_role=role_id) # Volver a renderizar con datos

    roles = Role.query.all()
    return render_template('login.html', roles=roles)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return f'Hola, {current_user.nombre_completo}! Estás en el Dashboard General como {current_user.role.nombre_rol}.'

@auth_bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden acceder.', 'danger')
        return redirect(url_for('auth.dashboard'))
    return render_template('admin/admin_dashboard.html', user=current_user) # Renderiza una plantilla para el admin dashboard

@auth_bp.route('/cashier_dashboard')
@login_required
def cashier_dashboard():
    if current_user.role.nombre_rol != 'Cajero':
        flash('Acceso denegado. Solo cajeros pueden acceder.', 'danger')
        return redirect(url_for('auth.dashboard'))
    return f'Bienvenido Cajero, {current_user.nombre_completo}.'

@auth_bp.route('/waiter_dashboard')
@login_required
def waiter_dashboard():
    if current_user.role.nombre_rol != 'Mesero':
        flash('Acceso denegado. Solo meseros pueden acceder.', 'danger')
        return redirect(url_for('auth.dashboard'))
    return f'Bienvenido Mesero, {current_user.nombre_completo}.'

# --- Gestión de Usuarios ---
@auth_bp.route('/admin/users')
@login_required
def manage_users():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden gestionar usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    users = User.query.options(db.joinedload(User.role)).all() # Carga los roles junto con los usuarios
    return render_template('admin/manage_users.html', users=users)

@auth_bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden crear usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    roles = Role.query.all()
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        nombre_completo = request.form['nombre_completo']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        id_rol = request.form['id_rol']

        # Validaciones
        if not all([nombre_usuario, nombre_completo, contrasena, confirmar_contrasena, id_rol]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=None)

        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=None)

        if User.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=None)

        try:
            new_user = User(
                nombre_usuario=nombre_usuario,
                nombre_completo=nombre_completo,
                id_rol=id_rol
            )
            new_user.set_password(contrasena) # Hashear la contraseña
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('auth.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {e}', 'danger')

    return render_template('admin/user_form.html', roles=roles, user=None, is_edit=False)

@auth_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden editar usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    user = User.query.get_or_404(user_id)
    roles = Role.query.all()

    if request.method == 'POST':
        user.nombre_usuario = request.form['nombre_usuario']
        user.nombre_completo = request.form['nombre_completo']
        user.id_rol = request.form['id_rol']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']

        # Validaciones
        if not all([user.nombre_usuario, user.nombre_completo, user.id_rol]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True)

        if contrasena: # Solo actualiza la contraseña si se proporciona
            if contrasena != confirmar_contrasena:
                flash('Las contraseñas no coinciden.', 'danger')
                return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True)
            user.set_password(contrasena)

        # Verificar si el nombre de usuario ya existe para otro usuario
        existing_user = User.query.filter(User.nombre_usuario == user.nombre_usuario, User.id_usuario != user_id).first()
        if existing_user:
            flash('El nombre de usuario ya existe para otro usuario.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True)

        try:
            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('auth.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {e}', 'danger')

    return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True)

@auth_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden eliminar usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    user = User.query.get_or_404(user_id)
    # Evitar que un administrador se elimine a sí mismo
    if user.id_usuario == current_user.id_usuario:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('auth.manage_users'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar usuario: {e}', 'danger')

    return redirect(url_for('auth.manage_users'))