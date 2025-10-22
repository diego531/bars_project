from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User, Role
from app import db
from werkzeug.security import generate_password_hash # Importa esto para hashear contraseñas

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirige según el rol si ya está autenticado
        if current_user.role.nombre_rol == 'Administrador':
            return redirect(url_for('auth.admin_dashboard'))
        elif current_user.role.nombre_rol == 'Cajero':
            return redirect(url_for('auth.cashier_dashboard'))
        elif current_user.role.nombre_rol == 'Mesero':
            return redirect(url_for('auth.waiter_dashboard'))
        return redirect(url_for('auth.dashboard'))

    # Esta línea debe estar disponible en ambos caminos (GET y POST con error)
    roles = Role.query.all() # Consulta los roles UNA SOLA VEZ

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_id = request.form['role'] # Este es el id_rol seleccionado

        user = User.query.filter_by(nombre_usuario=username, id_rol=role_id).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'¡Bienvenido, {user.nombre_completo}!', 'success')
            # Redirigir según el rol
            if user.role.nombre_rol == 'Administrador':
                return redirect(url_for('auth.admin_dashboard'))
            elif user.role.nombre_rol == 'Cajero':
                return redirect(url_for('auth.cashier_dashboard'))
            elif user.role.nombre_rol == 'Mesero':
                return redirect(url_for('auth.waiter_dashboard'))
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Datos incorrectos. Por favor, verifica tu usuario, contraseña y rol.', 'danger')
            # Si hay un error, volvemos a renderizar, pero ahora PASAMOS 'roles'
            # y también 'selected_role' para mantener la opción seleccionada.
            return render_template(
                '/login.html',
                username=username,
                selected_role=int(role_id), # Asegúrate de que sea un entero para la comparación
                roles=roles # ¡Aquí es donde le volvemos a pasar la lista de roles!
            )

    # Para la primera carga de la página (GET)
    return render_template('/login.html', roles=roles)

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
        return redirect(url_for('auth.cashier_dashboard'))
    return render_template('cashier/cashier_dashboard.html', user=current_user) # Renderiza una plantilla para el cajero dashboard

@auth_bp.route('/waiter_dashboard')
@login_required
def waiter_dashboard():
    if current_user.role.nombre_rol != 'Mesero':
        flash('Acceso denegado. Solo meseros pueden acceder.', 'danger')
        return redirect(url_for('auth.waiter_dashboard'))
    return render_template('waiter/waiter_dashboard.html', user=current_user) # Renderiza una plantilla para el mesero dashboard

# --- Gestión de Usuarios ---
@auth_bp.route('/admin/users')
@login_required
def manage_users():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden gestionar usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    users = User.query.options(db.joinedload(User.role)).all()
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
        id_rol_seleccionado = int(request.form['id_rol']) # Usar un nombre de variable más claro aquí

        # Validaciones
        if not all([nombre_usuario, nombre_completo, contrasena, confirmar_contrasena]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=None, is_edit=False, selected_role=id_rol_seleccionado)

        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=None, is_edit=False, selected_role=id_rol_seleccionado)

        if User.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=None, is_edit=False, selected_role=id_rol_seleccionado)

        # --- VALIDACIÓN: Un solo administrador ---
        admin_role = Role.query.filter_by(nombre_rol='Administrador').first()
        if admin_role and id_rol_seleccionado == admin_role.id_rol: # Si el rol que se intenta asignar es Administrador
            if User.query.filter_by(id_rol=admin_role.id_rol).count() >= 1: # Si ya existe al menos un administrador
                flash('Ya existe un administrador en el sistema. No se puede crear otro usuario con rol de Administrador.', 'danger')
                return render_template('admin/user_form.html', roles=roles, user=None, is_edit=False, selected_role=id_rol_seleccionado)

        try:
            new_user = User(
                nombre_usuario=nombre_usuario,
                nombre_completo=nombre_completo,
                id_rol=id_rol_seleccionado # Usar la variable corregida
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
        # Definir las nuevas variables a partir del formulario
        new_nombre_usuario = request.form['nombre_usuario']
        new_nombre_completo = request.form['nombre_completo']
        new_id_rol_seleccionado = int(request.form['id_rol']) # Corregido: Definido aquí
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']

        # Validaciones
        if not all([new_nombre_usuario, new_nombre_completo, new_id_rol_seleccionado]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True, selected_role=new_id_rol_seleccionado)

        if contrasena and contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True, selected_role=new_id_rol_seleccionado)

        # Verificar si el nombre de usuario ya existe para otro usuario
        existing_user_with_name = User.query.filter(
            User.nombre_usuario == new_nombre_usuario,
            User.id_usuario != user_id
        ).first()
        if existing_user_with_name:
            flash('El nombre de usuario ya existe para otro usuario.', 'danger')
            return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True, selected_role=new_id_rol_seleccionado)

        # --- VALIDACIÓN: Un solo administrador (durante la edición) ---
        admin_role = Role.query.filter_by(nombre_rol='Administrador').first()
        if admin_role and new_id_rol_seleccionado == admin_role.id_rol: # Si se intenta cambiar el rol a Administrador
            # Contar cuántos administradores existen excluyendo al usuario actual si ya era admin
            admin_count_excluding_current = User.query.filter(
                User.id_rol == admin_role.id_rol,
                User.id_usuario != user_id
            ).count()

            # Si ya hay un administrador (excluyendo el actual) Y el usuario actual NO era admin,
            # significa que se quiere crear un segundo admin.
            if admin_count_excluding_current >= 1 and user.id_rol != admin_role.id_rol:
                flash('Ya existe un administrador en el sistema. No se puede asignar el rol de Administrador a este usuario.', 'danger')
                return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True, selected_role=new_id_rol_seleccionado)

        # También hay que manejar el caso de que el actual usuario sea el único admin y se le quiera cambiar el rol
        # Primero, ver si el usuario actual ES un administrador
        is_current_user_admin = (user.id_rol == admin_role.id_rol) if admin_role else False

        # Segundo, ver si el nuevo rol NO es administrador
        is_new_role_not_admin = (new_id_rol_seleccionado != admin_role.id_rol) if admin_role else False

        # Si el usuario actual es administrador Y se le quiere cambiar el rol A un no-admin
        # Y no hay otros administradores registrados (solo él)
        if admin_role: # Asegurarse de que el rol de admin existe
            admin_count_total = User.query.filter_by(id_rol=admin_role.id_rol).count()
            if is_current_user_admin and is_new_role_not_admin and admin_count_total <= 1:
                flash('No puedes cambiar el rol del único administrador del sistema. Debe haber al menos un administrador.', 'danger')
                return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True, selected_role=new_id_rol_seleccionado)


        try:
            user.nombre_usuario = new_nombre_usuario
            user.nombre_completo = new_nombre_completo
            user.id_rol = new_id_rol_seleccionado # Asignar el nuevo rol

            if contrasena: # Solo actualiza la contraseña si se proporciona
                user.set_password(contrasena)

            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('auth.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {e}', 'danger')

    # Si es GET request, renderizar el formulario con los datos actuales del usuario
    return render_template('admin/user_form.html', roles=roles, user=user, is_edit=True, selected_role=user.id_rol)


@auth_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden eliminar usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    user_to_delete = User.query.get_or_404(user_id) # Corregido: Definir user_to_delete aquí

    # Evitar que un administrador se elimine a sí mismo
    if user_to_delete.id_usuario == current_user.id_usuario:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('auth.manage_users'))

    # --- VALIDACIÓN: No eliminar al único administrador ---
    admin_role = Role.query.filter_by(nombre_rol='Administrador').first()
    if admin_role and user_to_delete.id_rol == admin_role.id_rol: # Si el usuario a eliminar es un administrador
        # Contar cuántos administradores existen (incluyendo el que se intenta eliminar)
        current_admin_count = User.query.filter_by(id_rol=admin_role.id_rol).count()
        if current_admin_count <= 1: # Si es el único administrador
            flash('No puedes eliminar el único administrador del sistema. Debe existir al menos un administrador.', 'danger')
            return redirect(url_for('auth.manage_users'))

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Usuario eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar usuario: {e}', 'danger')

    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/forgot_password')
def forgot_password():
    # Por ahora, simplemente redirigimos a una página informativa o un placeholder.
    # La implementación real de recuperación de contraseña es más compleja (email, tokens, etc.).
    flash('Funcionalidad de recuperación de contraseña en desarrollo. Por favor, contacta al soporte técnico.', 'info')
    return render_template('auth/forgot_password.html') # Creamos una plantilla simple para esto