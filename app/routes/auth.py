from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User, Role
from app import db

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

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
    return f'Bienvenido Administrador, {current_user.nombre_completo}.'

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