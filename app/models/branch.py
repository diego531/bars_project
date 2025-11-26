from app import db

class Sede(db.Model):
    __tablename__ = 'Sedes'
    id_sede = db.Column(db.Integer, primary_key=True)
    nombre_sede = db.Column(db.String(45), unique=True, nullable=False) # Haremos que el nombre sea único y no nulo
    mesas = db.relationship('Mesa', backref='sede', lazy='dynamic', cascade='all, delete-orphan') # Relación con Mesa
     #Inventarios asociados a esta sede
    inventarios = db.relationship('Inventario', backref='sede', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sede {self.nombre_sede}>'

class Mesa(db.Model):
    __tablename__ = 'Mesas'
    id_mesa = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(45), default='libre', nullable=False) # 'libre', 'ocupada', etc.
    id_sede = db.Column(db.Integer, db.ForeignKey('Sedes.id_sede'), nullable=False)

    def __repr__(self):
        return f'<Mesa {self.id_mesa} (Sede: {self.id_sede}) - {self.estado}>'