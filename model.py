from datetime import datetime, timedelta, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
	__tablename__ = "usuarios"

	id = db.Column(db.Integer, primary_key=True)
	correo = db.Column(db.String(120), unique=True, nullable=False, index=True)
	password_hash = db.Column(db.String(255), nullable=False)
	rol = db.Column(db.String(20), nullable=False)
	intentos_fallidos = db.Column(db.Integer, nullable=False, default=0)
	cuenta_bloqueada = db.Column(db.Boolean, nullable=False, default=False)
	bloqueo_hasta = db.Column(db.DateTime(timezone=True), nullable=True)
	creado_en = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

	def set_password(self, password: str) -> None:
		# Se usa hash irreversible para que la contraseña nunca quede expuesta en texto plano,
		# incluso si la base de datos fuera comprometida.
		self.password_hash = generate_password_hash(password)

	def check_password(self, password: str) -> bool:
		return check_password_hash(self.password_hash, password)

	def esta_bloqueada(self) -> bool:
		if not self.cuenta_bloqueada:
			return False

		now = datetime.now(timezone.utc)
		if self.bloqueo_hasta and now >= self.bloqueo_hasta:
			self.cuenta_bloqueada = False
			self.intentos_fallidos = 0
			self.bloqueo_hasta = None
			return False

		return True

	def registrar_intento_fallido(self, max_intentos: int = 3, minutos_bloqueo: int = 15) -> None:
		self.intentos_fallidos += 1

		if self.intentos_fallidos >= max_intentos:
			self.cuenta_bloqueada = True
			# Bloqueo temporal para frenar ataques de fuerza bruta sin deshabilitar la cuenta de forma permanente.
			self.bloqueo_hasta = datetime.now(timezone.utc) + timedelta(minutes=minutos_bloqueo)

	def resetear_seguridad(self) -> None:
		self.intentos_fallidos = 0
		self.cuenta_bloqueada = False
		self.bloqueo_hasta = None