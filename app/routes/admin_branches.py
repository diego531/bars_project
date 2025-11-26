from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.branch import Sede, Mesa
from app import db

# Blueprint
admin_branches_bp = Blueprint('admin_branches', __name__, template_folder='../templates/admin')

# --- Rutas de Gestión de Sedes ---

@admin_branches_bp.route('/')
@login_required
def manage_branches():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden gestionar sedes.', 'danger')
        return redirect(url_for('auth.dashboard')) # Redirige al dashboard general si no es admin

    sedes = Sede.query.all()
    sedes_con_info = []
    for sede in sedes:
        sedes_con_info.append({
            'sede': sede,
            'num_mesas': sede.mesas.count(),
            'num_productos_en_inventario': sede.inventarios.count()
        })
    return render_template('manage_branches.html', sedes_con_info=sedes_con_info)

@admin_branches_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_branch():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden crear sedes.', 'danger')
        return redirect(url_for('auth.dashboard'))

    if request.method == 'POST':
        nombre_sede = request.form['nombre_sede']
        num_mesas = request.form.get('num_mesas', type=int)

        if not nombre_sede:
            flash('El nombre de la sede es obligatorio.', 'danger')
            return render_template('branch_form.html', sede=None, is_edit=False)

        if Sede.query.filter_by(nombre_sede=nombre_sede).first():
            flash('Ya existe una sede con ese nombre.', 'danger')
            return render_template('branch_form.html', sede=None, is_edit=False)

        if num_mesas is None or num_mesas < 0:
            flash('El número de mesas debe ser un valor numérico positivo.', 'danger')
            return render_template('branch_form.html', sede=None, is_edit=False, num_mesas_val=num_mesas)

        try:
            new_sede = Sede(nombre_sede=nombre_sede)
            db.session.add(new_sede)
            db.session.flush()

            for _ in range(num_mesas):
                mesa = Mesa(id_sede=new_sede.id_sede, estado='libre')
                db.session.add(mesa)

            db.session.commit()
            flash('Sede y mesas creadas exitosamente.', 'success')
            return redirect(url_for('admin_branches.manage_branches')) 
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear sede: {e}', 'danger')

    return render_template('branch_form.html', sede=None, is_edit=False)

@admin_branches_bp.route('/edit/<int:branch_id>', methods=['GET', 'POST'])
@login_required
def edit_branch(branch_id):
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden editar sedes.', 'danger')
        return redirect(url_for('auth.dashboard'))

    sede = Sede.query.get_or_404(branch_id)
    current_num_mesas = sede.mesas.count()

    if request.method == 'POST':
        new_nombre_sede = request.form['nombre_sede']
        new_num_mesas = request.form.get('num_mesas', type=int)

        if not new_nombre_sede:
            flash('El nombre de la sede es obligatorio.', 'danger')
            return render_template('branch_form.html', sede=sede, is_edit=True, num_mesas_val=new_num_mesas)

        existing_sede = Sede.query.filter(Sede.nombre_sede == new_nombre_sede, Sede.id_sede != branch_id).first()
        if existing_sede:
            flash('Ya existe otra sede con ese nombre.', 'danger')
            return render_template('branch_form.html', sede=sede, is_edit=True, num_mesas_val=new_num_mesas)

        if new_num_mesas is None or new_num_mesas < 0:
            flash('El número de mesas debe ser un valor numérico positivo.', 'danger')
            return render_template('branch_form.html', sede=sede, is_edit=True, num_mesas_val=new_num_mesas)

        try:
            sede.nombre_sede = new_nombre_sede

            if new_num_mesas > current_num_mesas:
                for _ in range(new_num_mesas - current_num_mesas):
                    mesa = Mesa(id_sede=sede.id_sede, estado='libre')
                    db.session.add(mesa)
            elif new_num_mesas < current_num_mesas:
                mesas_a_eliminar = sede.mesas.order_by(Mesa.id_mesa.desc()).limit(current_num_mesas - new_num_mesas).all()
                for mesa in mesas_a_eliminar:
                    db.session.delete(mesa)

            db.session.commit()
            flash('Sede y mesas actualizadas exitosamente.', 'success')
            return redirect(url_for('admin_branches.manage_branches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar sede: {e}', 'danger')

    return render_template('branch_form.html', sede=sede, is_edit=True, num_mesas_val=current_num_mesas)

@admin_branches_bp.route('/delete/<int:branch_id>', methods=['POST'])
@login_required
def delete_branch(branch_id):
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden eliminar sedes.', 'danger')
        return redirect(url_for('auth.dashboard'))

    sede = Sede.query.get_or_404(branch_id)

    try:
        db.session.delete(sede)
        db.session.commit()
        flash('Sede y todas sus mesas eliminadas exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar sede: {e}', 'danger')

    return redirect(url_for('admin_branches.manage_branches')) 