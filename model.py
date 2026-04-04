from datetime import datetime, timedelta, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# --- MÓDULO DE USUARIOS Y SESIONES ---

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
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

    def registrarIntentoFallido(self, maxIntentos: int = 4, minutosBloqueo: int = 15) -> None:
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

# --- MÓDULO DE INVENTARIO ---

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
    unidad = db.relationship('UnidadMedida', backref='materias_primas')
# --- MÓDULO DE PRODUCTOS ---

class Producto(db.Model):
    __tablename__ = "Producto"  # <--- Asegúrate que coincida con el SQL (Mayúscula)

    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    categoria = db.Column(db.String(50))
    precio = db.Column("precio_venta", db.Numeric(10, 2))
    stock = db.Column(db.Integer, nullable=False, default=0)
    
    # Aquí está el truco: 
    # En Python lo usas como .estado, pero en SQL lee 'estatus'
    estado = db.Column("estatus", db.Boolean, default=True)


class Cliente(db.Model):
    __tablename__ = "clientes"
    
    id = db.Column("id_cliente", db.Integer, primary_key=True)
    
    # En tu SQL la columna se llama 'id_usuario' y apunta a 'usuarios(id)'
    usuarioId = db.Column(
        "id_usuario",
        db.Integer,
        db.ForeignKey("usuarios.id"), 
        nullable=True,
        unique=True
    )
    
    nombre = db.Column(db.String(120), nullable=False)
    apellidoPaterno = db.Column("apellidoPaterno", db.String(50), nullable=False)
    apellidoMaterno = db.Column("apellidoMaterno", db.String(50), nullable=True)
    telefono = db.Column(db.String(15), nullable=True)
    alias = db.Column(db.String(50), nullable=True)  
    estado = db.Column(db.String(20), nullable=False, default="activo")
    creadoEn = db.Column(
        "creado_en",
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    usuario = db.relationship(
        "Usuario",
        backref=db.backref("cliente", uselist=False),
        foreign_keys=[usuarioId]
    )


class Venta(db.Model):
    __tablename__ = "ventas"

    id_venta = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # CORRECCIÓN: Tu SQL dice 'id_usuario', falta agregar esa columna en el modelo
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    # CORRECCIÓN: Tu SQL define la tabla como 'clientes' (minúscula)
    # El nombre físico de la columna en SQL es 'id_cliente'
    id_cliente = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=True)

    tipo_venta = db.Column(db.String(20), nullable=False)  
    metodo_pago = db.Column(db.String(20), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    # Relaciones
    cliente = db.relationship("Cliente", backref="ventas")
    usuario = db.relationship("Usuario", backref="ventas_realizadas")

class DetalleVenta(db.Model):
    __tablename__ = "detalle_venta"

    id_detalle = db.Column("id_detalle", db.Integer, primary_key=True)

    id_venta = db.Column(
        db.Integer,
        db.ForeignKey("ventas.id_venta"),
        nullable=False
    )

    id_producto = db.Column(
        db.Integer,
        db.ForeignKey("Producto.id_producto"),
        nullable=False
    )

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    descuento = db.Column(db.Numeric(10, 2), default=0.00)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    venta = db.relationship("Venta", backref="detalles")
    producto = db.relationship("Producto")
class Pedido(db.Model):
    __tablename__ = "pedidos"

    id_pedido = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    nombre = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(15))
    hora_recogida = db.Column(db.DateTime, nullable=False)
    notas = db.Column(db.String(200))

    estado = db.Column(db.String(20), default="pendiente")

    # Relación opcional a venta
    id_venta = db.Column(db.Integer, db.ForeignKey("ventas.id_venta"), nullable=True)