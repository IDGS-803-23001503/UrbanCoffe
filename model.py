from database import db
from datetime import datetime
from decimal import Decimal


# ============================================
# MODELOS BASE
# ============================================

class Rol(db.Model):
    __tablename__ = 'rol'

    id_rol = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(20), unique=True)

    usuarios = db.relationship('Usuario', backref='rol', lazy=True)


class Usuario(db.Model):
    __tablename__ = 'usuario'

    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_rol = db.Column(db.Integer, db.ForeignKey('rol.id_rol'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    ap_paterno = db.Column(db.String(50))
    ap_materno = db.Column(db.String(50))
    telefono = db.Column(db.String(15), nullable=False)
    correo = db.Column(db.String(50), nullable=False, unique=True)
    contrasena = db.Column(db.String(255), nullable=False)
    estatus = db.Column(db.Boolean, default=True)


class UnidadMedida(db.Model):
    __tablename__ = 'unidad_medida'

    id_unidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(10), nullable=False)
    abreviacion = db.Column(db.String(4), unique=True)


# ============================================
# MODELOS PARA EL MÓDULO DE UTILIDAD
# ============================================

class MateriaPrima(db.Model):
    __tablename__ = 'materia_prima'

    id_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)
    unidad_medida = db.Column(db.Integer, db.ForeignKey('unidad_medida.id_unidad'))
    stock_minimo = db.Column(db.Numeric(10, 2), default=0)
    stock_actual = db.Column(db.Numeric(10, 2), default=0)
    costo_promedio = db.Column(db.Numeric(10, 2), default=0)

    unidad = db.relationship('UnidadMedida', backref='materias')
    recetas = db.relationship('Recetas', backref='materia_prima', lazy=True)

    def actualizar_costo_promedio(self, nuevo_costo, cantidad):
        """Actualiza el costo promedio usando método promedio ponderado"""
        nuevo_costo_dec = Decimal(str(nuevo_costo))
        cantidad_dec = Decimal(str(cantidad))

        if self.stock_actual and self.stock_actual > 0:
            stock_actual_dec = Decimal(str(self.stock_actual))
            costo_actual_dec = Decimal(str(self.costo_promedio or 0))
            costo_anterior = costo_actual_dec * stock_actual_dec
            costo_nuevo = nuevo_costo_dec * cantidad_dec
            total_costo = costo_anterior + costo_nuevo
            total_stock = stock_actual_dec + cantidad_dec
            if total_stock > 0:
                self.costo_promedio = float(total_costo / total_stock)
        else:
            self.costo_promedio = float(nuevo_costo_dec)


class Producto(db.Model):
    __tablename__ = 'producto'

    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    categoria = db.Column(db.String(50))
    precio_venta = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, default=0)
    estatus = db.Column(db.Boolean, default=True)

    recetas = db.relationship('Recetas', backref='producto', lazy=True)
    detalles_venta = db.relationship('DetalleVenta', backref='producto', lazy=True)

    def costo_unitario(self):
        """Calcula el costo unitario basado en la receta y el costo promedio de insumos"""
        if not self.recetas:
            return Decimal('0')
        total = Decimal('0')
        for receta in self.recetas:
            if receta.materia_prima:
                cantidad = Decimal(str(receta.cantidad))
                costo = Decimal(str(receta.materia_prima.costo_promedio or 0))
                total += cantidad * costo
        return total

    def margen_ganancia(self):
        """Calcula el margen de ganancia unitario"""
        costo = self.costo_unitario()
        if self.precio_venta:
            return Decimal(str(self.precio_venta)) - costo
        return Decimal('0')

    def margen_porcentaje(self):
        """Calcula el porcentaje de ganancia sobre el precio de venta"""
        costo = self.costo_unitario()
        if self.precio_venta and self.precio_venta > 0:
            return ((Decimal(str(self.precio_venta)) - costo) / Decimal(str(self.precio_venta))) * 100
        return Decimal('0')

    def to_dict_rentabilidad(self):
        return {
            'id': self.id_producto,
            'nombre': self.nombre,
            'precio': float(self.precio_venta) if self.precio_venta else 0,
            'costo': float(self.costo_unitario()),
            'margen': float(self.margen_ganancia()),
            'porcentaje': float(self.margen_porcentaje())
        }


class Recetas(db.Model):
    __tablename__ = 'recetas'

    id_receta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia_prima.id_materia'), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('id_producto', 'id_materia', name='unique_producto_materia'),
    )


class Venta(db.Model):
    __tablename__ = 'ventas'

    id_venta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    metodo_pago = db.Column(db.String(30), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', backref='ventas')


class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'

    id_detalle_venta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_venta = db.Column(db.Integer, db.ForeignKey('ventas.id_venta'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('producto.id_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('id_venta', 'id_producto', name='unique_venta_producto'),
    )
