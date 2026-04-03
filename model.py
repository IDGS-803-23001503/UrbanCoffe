from datetime import datetime, timedelta, timezone, date
from sqlalchemy import Enum
from sqlalchemy.dialects.mysql import LONGTEXT

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

 #Tablas Feacture/login 

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    usuario = db.Column(db.String(60), unique=True, nullable=True, index=True)
    correo = db.Column(db.String(120), unique=True, nullable=False, index=True)
    contrasenaHash = db.Column("password_hash", db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="Activo")
    intentosFallidos = db.Column("intentos_fallidos", db.Integer, nullable=False, default=0)
    cuentaBloqueada = db.Column("cuenta_bloqueada", db.Boolean, nullable=False, default=False)
    bloqueoHasta = db.Column("bloqueo_hasta", db.DateTime(timezone=True), nullable=True)
    creadoEn = db.Column("creado_en", db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    def establecerContrasena(self, contrasena: str) -> None:
        # Se usa hash irreversible para que la contraseña nunca quede expuesta en texto plano,
        # incluso si la base de datos fuera comprometida.
        self.contrasenaHash = generate_password_hash(contrasena)

    def validarContrasena(self, contrasena: str) -> bool:
        return check_password_hash(self.contrasenaHash, contrasena)

    def estaBloqueada(self) -> bool:
        if not self.cuentaBloqueada:
            return False

        ahora = datetime.now(timezone.utc)
        bloqueoHastaNormalizado = self.bloqueoHasta
        if bloqueoHastaNormalizado and bloqueoHastaNormalizado.tzinfo is None:
            bloqueoHastaNormalizado = bloqueoHastaNormalizado.replace(tzinfo=timezone.utc)

        if bloqueoHastaNormalizado and ahora >= bloqueoHastaNormalizado:
            self.cuentaBloqueada = False
            self.intentosFallidos = 0
            self.bloqueoHasta = None
            return False

        return True

    def registrarIntentoFallido(self, maxIntentos: int = 4, minutosBloqueo: int = 15) -> None:
        self.intentosFallidos += 1

        if self.intentosFallidos >= maxIntentos:
            self.cuentaBloqueada = True
            # Bloqueo temporal para frenar ataques de fuerza bruta sin deshabilitar la cuenta de forma permanente.
            self.bloqueoHasta = datetime.now(timezone.utc) + timedelta(minutes=minutosBloqueo)

    def resetearSeguridad(self) -> None:
        self.intentosFallidos = 0
        self.cuentaBloqueada = False
        self.bloqueoHasta = None


class RegistroSesion(db.Model):
    __tablename__ = "registros_sesion"

    id = db.Column(db.Integer, primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    tokenSesion = db.Column(db.String(128), nullable=False, index=True)
    direccionIp = db.Column(db.String(64), nullable=True)
    agenteUsuario = db.Column(db.String(255), nullable=True)
    fechaInicio = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    fechaFin = db.Column(db.DateTime(timezone=True), nullable=True)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    
    
    
#Tablas Feacture/Productos 

class UnidadMedida(db.Model):
    __tablename__ = 'Unidad_medida'
    id_unidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(10), nullable=False)
    abreviacion = db.Column(db.String(4), unique=True)

class MateriaPrima(db.Model):
    __tablename__ = 'Materia_prima' 

    id_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    unidad_medida = db.Column(db.Integer, db.ForeignKey('Unidad_medida.id_unidad'), nullable=False) 
    stock_minimo = db.Column(db.Numeric(10, 2), default=0.00)
    stock_actual = db.Column(db.Numeric(10, 2), default=0.00)
    estatus = db.Column(db.Boolean, default=True)
    unidad = db.relationship('UnidadMedida', backref='materias_primas')

class Producto(db.Model):
    __tablename__ = 'Producto'

    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    categoria = db.Column(Enum('bebidas', 'alimentos', name='categoria_enum'), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, nullable=False, default=0)
    descripcion = db.Column(db.Text, nullable=False)
    imagen = db.Column(LONGTEXT, nullable=True)
    estatus = db.Column(db.Boolean, default=True)
    
class Proveedores(db.Model):
    __tablename__ = 'Proveedor'

    id  = db.Column('id_proveedor', db.Integer, primary_key=True, autoincrement=True)
    rfc = db.Column('RFC',    db.String(13),  unique=True, nullable=False)
    nombre = db.Column(          db.String(100), nullable=False)
    email = db.Column('correo', db.String(50),  nullable=True)
    telefono = db.Column(          db.String(15),  nullable=True)
    direccion = db.Column(          db.Text,        nullable=True)
    estado = db.Column('estatus',db.Boolean,     default=True)


class ProductoTerminado(db.Model):
    __tablename__ = "productos_terminados"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stockActual = db.Column("stock_actual", db.Integer, nullable=False, default=0)
    stockMinimo = db.Column("stock_minimo", db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creadoEn = db.Column("creado_en", db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class MateriaPrima(db.Model):
    __tablename__ = "materias_primas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    unidadMedida = db.Column("unidad_medida", db.String(30), nullable=False, default="unidad")
    stockActual = db.Column("stock_actual", db.Numeric(10, 2), nullable=False, default=0)
    stockMinimo = db.Column("stock_minimo", db.Numeric(10, 2), nullable=False, default=0)
    costoUnitario = db.Column("costo_unitario", db.Numeric(10, 2), nullable=False, default=0)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    creadoEn = db.Column("creado_en", db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    usuarioId = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    utilidadBruta = db.Column("utilidad_bruta", db.Numeric(10, 2), nullable=False, default=0)
    confirmada = db.Column(db.Boolean, nullable=False, default=True)
    origen = db.Column(db.String(20), nullable=False, default="POS")
    creadoEn = db.Column("creado_en", db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class DetalleVenta(db.Model):
    __tablename__ = "detalles_venta"

    id = db.Column(db.Integer, primary_key=True)
    ventaId = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False, index=True)
    productoId = db.Column(db.Integer, db.ForeignKey("productos_terminados.id"), nullable=False, index=True)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precioUnitario = db.Column("precio_unitario", db.Numeric(10, 2), nullable=False, default=0)
    costoUnitario = db.Column("costo_unitario", db.Numeric(10, 2), nullable=False, default=0)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
# Tabla de merma 
class Merma(db.Model):
    id_merma = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Numeric(10, 2), nullable = False)
    fecha = db.Column( db.Date , default=date.today, nullable = False)
    motivo = db.Column(Enum(
                            "Error en preparación",
                            "Derrame o caída",
                            "Insumo en mal estado",
                            "Producto caducado",
                            "Sobrante de producción diaria",
                            "Falla de refrigeración/almacenaje",
                            "Muestra o degustación",
                            "Pérdida no identificada",
                            "Devolución por cliente", 
      name='merma_enum'  
    ), nullable = False)
    
    materia_id = db.Column(db.Integer, db.ForeignKey('Materia_prima.id_materia'), nullable=False)
    materia = db.relationship('MateriaPrima', backref='mermas')
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', backref='mermas_registradas')
    
