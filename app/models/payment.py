from app import db
from datetime import datetime

# Importar modelos relacionados para las FK
from app.models.order import Pedido
from app.models.user import User

class Pago(db.Model):
    __tablename__ = 'Pagos'
    id_pago = db.Column(db.Integer, primary_key=True, autoincrement=True)
    monto_pago = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(45), nullable=False) # Ej: 'efectivo', 'tarjeta', 'nequi'
    fecha_hora_pago = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_pedido = db.Column(db.Integer, db.ForeignKey('Pedidos.id_pedido'), nullable=False)
    id_usuario_cajero = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)

    # Relaciones
    pedido = db.relationship('Pedido', backref='pagos', lazy=True)
    cajero = db.relationship('User', backref='pagos_realizados', lazy=True)

    def __repr__(self):
        return f'<Pago {self.id_pago} - Pedido: {self.id_pedido} - Monto: {self.monto_pago}>'