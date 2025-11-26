from app import db

# Importar los modelos relacionados para que SQLAlchemy pueda establecer las relaciones
# y para que podamos acceder a sus propiedades (ej. inventory_item.producto.nombre)
from app.models.product import Producto
from app.models.branch import Sede


class Inventario(db.Model):
    __tablename__ = 'Inventario'
    id_inventario = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    esta_bloqueado = db.Column(db.Boolean, nullable=False, default=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('Productos.id_producto'), nullable=False)
    id_sede = db.Column(db.Integer, db.ForeignKey('Sedes.id_sede'), nullable=False)

    # Combinación única de producto y sede para evitar duplicados en el inventario de una sede
    __table_args__ = (db.UniqueConstraint('id_producto', 'id_sede', name='_producto_sede_uc'),)

    def __repr__(self):
        return f'<Inventario Producto: {self.id_producto} Sede: {self.id_sede} Cantidad: {self.cantidad} Bloqueado: {self.esta_bloqueado}>'