from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User, Role
from app.models.branch import Sede # NUEVO: Importar el modelo Sede
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
            return redirect(url_for('waiter_orders.waiter_dashboard'))
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
                return redirect(url_for('waiter_orders.waiter_dashboard'))
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Datos incorrectos. Por favor, verifica tu usuario, contraseña y rol.', 'danger')
            # Si hay un error, volvemos a renderizar, pero ahora PASAMOS 'roles'
            # y también 'selected_role' para mantener la opción seleccionada.
            return render_template(
                '/login.html',
                username=username,
                selected_role=int(role_id), 
                roles=roles # Aquí es donde le volvemos a pasar la lista de roles
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
    sedes = Sede.query.all() # NUEVO: Obtener todas las sedes
    
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        nombre_completo = request.form['nombre_completo']
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        id_rol_seleccionado = int(request.form['id_rol'])
        
        # NUEVO: Obtener el id_sede, puede ser None si no se seleccionó o si el rol no lo requiere
        id_sede_seleccionada = request.form.get('id_sede')
        if id_sede_seleccionada:
            id_sede_seleccionada = int(id_sede_seleccionada)
        else:
            id_sede_seleccionada = None # Asegurar que sea None si está vacío

        # Validaciones
        # Se necesita la sede para Meseros (id_rol=3) y Cajeros (id_rol=2)
        if (id_rol_seleccionado == 2 or id_rol_seleccionado == 3) and not id_sede_seleccionada:
            flash('La sede es obligatoria para usuarios con rol de Mesero o Cajero.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=None, is_edit=False, selected_role=id_rol_seleccionado, selected_sede=id_sede_seleccionada)


        if not all([nombre_usuario, nombre_completo, contrasena, confirmar_contrasena]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=None, is_edit=False, selected_role=id_rol_seleccionado, selected_sede=id_sede_seleccionada)

        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=None, is_edit=False, selected_role=id_rol_seleccionado, selected_sede=id_sede_seleccionada)

        if User.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=None, is_edit=False, selected_role=id_rol_seleccionado, selected_sede=id_sede_seleccionada)

        try:
            new_user = User(
                nombre_usuario=nombre_usuario,
                nombre_completo=nombre_completo,
                id_rol=id_rol_seleccionado,
                id_sede=id_sede_seleccionada # NUEVO: Guardar la sede
            )
            new_user.set_password(contrasena)
            db.session.add(new_user)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            return redirect(url_for('auth.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {e}', 'danger')

    return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=None, is_edit=False) # NUEVO: Pasar sedes

@auth_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden editar usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    user = User.query.get_or_404(user_id)
    roles = Role.query.all()
    sedes = Sede.query.all() # NUEVO: Obtener todas las sedes

    if request.method == 'POST':
        new_nombre_usuario = request.form['nombre_usuario']
        new_nombre_completo = request.form['nombre_completo']
        new_id_rol_seleccionado = int(request.form['id_rol'])
        contrasena = request.form['contrasena']
        confirmar_contrasena = request.form['confirmar_contrasena']
        
        # NUEVO: Obtener el id_sede del formulario
        new_id_sede_seleccionada = request.form.get('id_sede')
        if new_id_sede_seleccionada:
            new_id_sede_seleccionada = int(new_id_sede_seleccionada)
        else:
            new_id_sede_seleccionada = None # Asegurar que sea None si está vacío

        # Validaciones
        # Se necesita la sede para Meseros (id_rol=3) y Cajeros (id_rol=2)
        if (new_id_rol_seleccionado == 2 or new_id_rol_seleccionado == 3) and not new_id_sede_seleccionada:
            flash('La sede es obligatoria para usuarios con rol de Mesero o Cajero.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=user, is_edit=True, selected_role=new_id_rol_seleccionado, selected_sede=new_id_sede_seleccionada)


        if not all([new_nombre_usuario, new_nombre_completo, new_id_rol_seleccionado]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=user, is_edit=True, selected_role=new_id_rol_seleccionado, selected_sede=new_id_sede_seleccionada)

        if contrasena and contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=user, is_edit=True, selected_role=new_id_rol_seleccionado, selected_sede=new_id_sede_seleccionada)

        existing_user_with_name = User.query.filter(
            User.nombre_usuario == new_nombre_usuario,
            User.id_usuario != user_id
        ).first()
        if existing_user_with_name:
            flash('El nombre de usuario ya existe para otro usuario.', 'danger')
            return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=user, is_edit=True, selected_role=new_id_rol_seleccionado, selected_sede=new_id_sede_seleccionada)

        try:
            user.nombre_usuario = new_nombre_usuario
            user.nombre_completo = new_nombre_completo
            user.id_rol = new_id_rol_seleccionado
            user.id_sede = new_id_sede_seleccionada # NUEVO: Guardar la sede

            if contrasena:
                user.set_password(contrasena)

            db.session.commit()
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('auth.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {e}', 'danger')

    return render_template('admin/user_form.html', roles=roles, sedes=sedes, user=user, is_edit=True, selected_role=user.id_rol, selected_sede=user.id_sede) # NUEVO: Pasar sedes y selected_sede

@auth_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden eliminar usuarios.', 'danger')
        return redirect(url_for('auth.dashboard'))

    user_to_delete = User.query.get_or_404(user_id)

    # Evitar que un administrador se elimine a sí mismo (esto es una buena práctica general)
    if user_to_delete.id_usuario == current_user.id_usuario:
        flash('No puedes eliminar tu propia cuenta de administrador.', 'danger')
        return redirect(url_for('auth.manage_users'))

    # --- REGLA DE NEGOCIO ELIMINADA: No eliminar al único administrador ---

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
    flash('Funcionalidad de recuperación de contraseña en desarrollo. Por favor, contacta al soporte técnico.', 'info')
    return render_template('auth/forgot_password.html') 