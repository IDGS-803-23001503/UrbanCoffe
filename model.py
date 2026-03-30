from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ==========================================
# TABLA DE UNIDADES DE MEDIDA
# ==========================================
class UnidadMedida(db.Model):
    __tablename__ = 'Unidad_medida'

    id_unidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(10), nullable=False)
    abreviacion = db.Column(db.String(4), unique=True)

# ==========================================
# MÓDULO: INVENTARIO DE MATERIA PRIMA
# ==========================================
class MateriaPrima(db.Model):
    __tablename__ = 'Materia_prima' 

    id_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    unidad_medida = db.Column(db.Integer, db.ForeignKey('Unidad_medida.id_unidad'), nullable=False) 
    stock_minimo = db.Column(db.Numeric(10, 2), default=0.00)
    stock_actual = db.Column(db.Numeric(10, 2), default=0.00)
    unidad = db.relationship('UnidadMedida', backref='materias_primas')
    
# ==========================================
# MÓDULO: INVENTARIO DE PRODUCTO TERMINADO
# ==========================================
class Producto(db.Model):
    __tablename__ = 'Producto'

    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    categoria = db.Column(db.String(50))
    precio_venta = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, nullable=False, default=0)
    estatus = db.Column(db.Boolean, default=True)