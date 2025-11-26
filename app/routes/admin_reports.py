# app/routes/admin_reports.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import io
import pandas as pd #pandas para generar CSV/XLS
import pytz # Para manejar zonas horarias, si es necesario, o utc

from app import db
from app.models.order import Pedido, DetallePedido
from app.models.product import Producto
from app.models.branch import Sede
from app.models.branch import Mesa

admin_reports_bp = Blueprint('admin_reports', __name__, template_folder='../templates/admin')

# Puente para asegurar que solo los administradores accedan a estas rutas
@admin_reports_bp.before_request
@login_required
def require_admin_for_reports():
    if current_user.role.nombre_rol != 'Administrador':
        flash('Acceso denegado. Solo administradores pueden generar reportes.', 'danger')
        return redirect(url_for('auth.dashboard'))

@admin_reports_bp.route('/reports')
def sales_reports_form():
    sedes = Sede.query.all()
    return render_template('sales_reports_form.html', sedes=sedes)

@admin_reports_bp.route('/reports/generate', methods=['GET', 'POST'])
def generate_sales_report():
    if request.method == 'POST':
        fecha_inicio_str = request.form.get('fecha_inicio')
        fecha_fin_str = request.form.get('fecha_fin')
        id_sede = request.form.get('id_sede', type=int)
        export_format = request.form.get('export_format')

        # Convertir fechas a objetos datetime
        # Asumimos que las fechas se ingresan en formato YYYY-MM-DD
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d') if fecha_inicio_str else None
            # Para la fecha fin, queremos incluir todo el día, así que añadimos 23:59:59
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1) if fecha_fin_str else None
        except ValueError:
            flash('Formato de fecha inválido. Por favor, usa YYYY-MM-DD.', 'danger')
            return redirect(url_for('admin_reports.sales_reports_form'))

        # Consulta base
        query = db.session.query(
            Pedido.fecha_creacion,
            Producto.codigo.label('codigo_producto'),
            Producto.nombre.label('nombre_producto'),
            DetallePedido.cantidad,
            DetallePedido.costo_unitario,
            DetallePedido.precio_unitario,
            DetallePedido.subtotal,
            Sede.nombre_sede
        ).join(DetallePedido, Pedido.id_pedido == DetallePedido.id_pedido)\
         .join(Producto, DetallePedido.id_producto == Producto.id_producto)\
         .join(Mesa, Pedido.id_mesa == Mesa.id_mesa)\
         .join(Sede, Mesa.id_sede == Sede.id_sede)\
         .filter(Pedido.estado == 'pagado') # Solo reportes de pedidos pagados

        # Filtrar por fecha de creación del pedido
        if fecha_inicio:
            query = query.filter(Pedido.fecha_creacion >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Pedido.fecha_creacion <= fecha_fin)

        # Filtrar por sede
        if id_sede:
            query = query.filter(Sede.id_sede == id_sede)

        resultados = query.all()

        if not resultados:
            flash('No se encontraron datos para los criterios de filtro seleccionados.', 'info')
            return redirect(url_for('admin_reports.sales_reports_form'))

        # Procesar los resultados para el reporte
        reporte_data = []
        for row in resultados:
            costo_vendido = row.cantidad * row.costo_unitario
            ventas = row.subtotal # Subtotal ya es cantidad * precio_unitario
            ganancia = ventas - costo_vendido
            reporte_data.append({
                'Fecha Pedido': row.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                'Código Producto': row.codigo_producto,
                'Nombre Producto': row.nombre_producto,
                'Cantidad': row.cantidad,
                'Costo de lo Vendido': f"{costo_vendido:.2f}",
                'Ventas': f"{ventas:.2f}",
                'Ganancia': f"{ganancia:.2f}",
                'Sede': row.nombre_sede
            })
        
        # Convertir a DataFrame de Pandas
        df = pd.DataFrame(reporte_data)

        if export_format == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'reporte_ventas_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
            )
        elif export_format == 'excel':
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter') # Asegura el motor
            df.to_excel(writer, index=False, sheet_name='Reporte de Ventas')
            writer.close() # Cierra el ExcelWriter
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'reporte_ventas_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
            )
        else:
            flash('Formato de exportación no válido.', 'danger')
            return redirect(url_for('admin_reports.sales_reports_form'))
            
    # Si es GET, simplemente mostramos el formulario
    return redirect(url_for('admin_reports.sales_reports_form'))