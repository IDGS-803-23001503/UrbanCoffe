from database import db
from datetime import datetime
from decimal import Decimal


# ============================================
# MODELOS BASE
# ============================================

class Proveedor(db.Model):
    __tablename__ = 'proveedor'

    id_proveedor = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RFC          = db.Column(db.String(13), unique=True, nullable=False)
    nombre       = db.Column(db.String(100), nullable=False)
    correo       = db.Column(db.String(50))
    telefono     = db.Column(db.String(15))
    direccion    = db.Column(db.Text)
    estatus      = db.Column(db.Boolean, default=True)

    compras = db.relationship('Compra', backref='proveedor', lazy=True)


class UnidadMedida(db.Model):
    __tablename__ = 'unidad_medida'

    id_unidad   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre      = db.Column(db.String(10), nullable=False)
    abreviacion = db.Column(db.String(4), unique=True)


class MateriaPrima(db.Model):
    __tablename__ = 'materia_prima'

    id_materia     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre         = db.Column(db.String(50), nullable=False)
    descripcion    = db.Column(db.Text)
    unidad_medida  = db.Column(db.Integer, db.ForeignKey('unidad_medida.id_unidad'))
    stock_minimo   = db.Column(db.Numeric(10, 2), default=0)
    stock_actual   = db.Column(db.Numeric(10, 2), default=0)
    costo_promedio = db.Column(db.Numeric(10, 2), default=0)

    unidad          = db.relationship('UnidadMedida', backref='materias')
    detalles_compra = db.relationship('DetalleCompra', backref='materia_prima', lazy=True)

    def actualizar_stock(self, cantidad, costo_unitario):
        """Actualiza stock y costo promedio al recibir una compra (promedio ponderado)"""
        cantidad_dec     = Decimal(str(cantidad))
        costo_dec        = Decimal(str(costo_unitario))
        stock_actual_dec = Decimal(str(self.stock_actual or 0))

        self.stock_actual = float(stock_actual_dec + cantidad_dec)

        if stock_actual_dec > 0:
            costo_actual_dec     = Decimal(str(self.costo_promedio or 0))
            total_costo_anterior = costo_actual_dec * stock_actual_dec
            total_costo_nuevo    = costo_dec * cantidad_dec
            nuevo_costo_promedio = (total_costo_anterior + total_costo_nuevo) / (stock_actual_dec + cantidad_dec)
            self.costo_promedio  = float(nuevo_costo_promedio)
        else:
            self.costo_promedio = float(costo_dec)

    def revertir_stock(self, cantidad):
        """Revierte el stock al cancelar una compra"""
        cantidad_dec      = Decimal(str(cantidad))
        stock_actual_dec  = Decimal(str(self.stock_actual or 0))
        nuevo_stock       = stock_actual_dec - cantidad_dec
        self.stock_actual = float(max(nuevo_stock, Decimal('0')))


# ============================================
# MODELOS DE COMPRAS
# ============================================

class Compra(db.Model):
    __tablename__ = 'compra'

    id_compra    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_proveedor = db.Column(db.Integer, db.ForeignKey('proveedor.id_proveedor'), nullable=False)
    fecha        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)
    # estatus eliminado — no existe en la BD

    detalles = db.relationship('DetalleCompra', backref='compra', lazy=True, cascade='all, delete-orphan')


class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'

    id_detalle_compra = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_compra         = db.Column(db.Integer, db.ForeignKey('compra.id_compra'), nullable=False)
    id_materia        = db.Column(db.Integer, db.ForeignKey('materia_prima.id_materia'), nullable=False)
    cantidad          = db.Column(db.Numeric(10, 2), nullable=False)
    unidad            = db.Column(db.Integer, db.ForeignKey('unidad_medida.id_unidad'), nullable=False)
    costo_unitario    = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal          = db.Column(db.Numeric(10, 2), nullable=False)

    unidad_medida = db.relationship('UnidadMedida', backref='detalles_compra')