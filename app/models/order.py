# app/models/order.py

from app import db
from datetime import datetime

# Importar modelos relacionados para las FK y las relaciones en SQLAlchemy
from app.models.user import User
from app.models.branch import Mesa
from app.models.product import Producto # Para DetallePedido


class Pedido(db.Model):
    __tablename__ = 'Pedidos'
    id_pedido = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(20), nullable=False, default='pendiente') # Ej: 'pendiente', 'en_preparacion', 'servido', 'pagado', 'cancelado'
    total_pedido = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_usuario_mesero = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    id_mesa = db.Column(db.Integer, db.ForeignKey('Mesas.id_mesa'), nullable=False)

    # Relaciones
    mesero = db.relationship('User', backref='pedidos_realizados', lazy=True)
    mesa = db.relationship('Mesa', backref=db.backref('pedidos', lazy=True, cascade='all, delete-orphan'))
    detalles = db.relationship('DetallePedido', backref='pedido', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Pedido {self.id_pedido} - Mesa {self.id_mesa} - Estado: {self.estado}>'

class DetallePedido(db.Model):
    __tablename__ = 'Detalle_Pedido'
    id_detalle_pedido = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False) # Precio del producto en el momento del pedido
    costo_unitario = db.Column(db.Numeric(10, 2), nullable=False)  # Costo del producto en el momento del pedido
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    id_pedido = db.Column(db.Integer, db.ForeignKey('Pedidos.id_pedido'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('Productos.id_producto'), nullable=False)

    # Relaciones
    producto = db.relationship('Producto', backref='detalle_pedidos', lazy=True)

    def __repr__(self):
        return f'<DetallePedido {self.id_detalle_pedido} - Pedido: {self.id_pedido} - Producto: {self.id_producto}>'