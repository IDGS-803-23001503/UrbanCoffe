from datetime import datetime, timedelta, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


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

    def registrarIntentoFallido(self, maxIntentos: int = 3, minutosBloqueo: int = 15) -> None:
        self.intentosFallidos += 1

        if self.intentosFallidos >= maxIntentos:
            self.cuentaBloqueada = True
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
