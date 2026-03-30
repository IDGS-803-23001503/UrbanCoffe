from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    

# ==========================================
# MÓDULO: SOLICITUDES DE PRODUCCIÓN
# ==========================================

# Tabla temporal para usuarios (solo para la relación con SolicitudProduccion)
# se cambiara por la tabla real de usuarios cuando se integre el proyecto completo 
# pero puse el mismo nombre de tabla y variable que puso zavala :)
class Usuario(db.Model):
    __tablename__ = "Usuario" 
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50))
    
class SolicitudProduccion(db.Model):
    __tablename__ = 'Solicitud_produccion'

    id_solicitud = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuario.id_usuario'), nullable=False) 
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    estado = db.Column(db.Enum('pendiente', 'en_proceso', 'finalizado', 'cancelado'), default='pendiente')

    usuario = db.relationship('Usuario', backref='solicitudes')
    
class DetalleProduccion(db.Model):
    __tablename__ = 'Detalle_produccion'

    id_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_solicitud = db.Column(db.Integer, db.ForeignKey('Solicitud_produccion.id_solicitud'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('Producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)

    solicitud = db.relationship('SolicitudProduccion', backref='detalles')
    producto = db.relationship('Producto', backref='detalles_solicitud')