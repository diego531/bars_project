from app import db

class CategoriaProducto(db.Model):
    __tablename__ = 'Categorias_Producto'
    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45), unique=True, nullable=False)
    descripcion = db.Column(db.String(100), nullable=True) # Puede ser nulo
    productos = db.relationship('Producto', backref='categoria', lazy='dynamic')

    def __repr__(self):
        return f'<CategoriaProducto {self.nombre}>'

class Producto(db.Model):
    __tablename__ = 'Productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(45), unique=True, nullable=True) # Puede ser nulo, pero si existe debe ser único
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(100), nullable=True)
    costo_compra = db.Column(db.Numeric(10, 2), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('Categorias_Producto.id_categoria'), nullable=False)
    #Relacion con inventario
    inventarios = db.relationship('Inventario', backref='producto', lazy='dynamic', cascade='all, delete-orphan')


    def __repr__(self):
        return f'<Producto {self.nombre}>'