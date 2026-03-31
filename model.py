from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ============================================
# MODELO PROVEEDOR
# Mapea la tabla 'Proveedor' del esquema SQL:
#   id_proveedor -> id
#   RFC          -> rfc
#   correo       -> email
#   estatus      -> estado
# ============================================

class Proveedores(db.Model):
    __tablename__ = 'Proveedor'

    id        = db.Column('id_proveedor', db.Integer, primary_key=True, autoincrement=True)
    rfc       = db.Column('RFC',    db.String(13),  unique=True, nullable=False)
    nombre    = db.Column(          db.String(100), nullable=False)
    email     = db.Column('correo', db.String(50),  nullable=True)
    telefono  = db.Column(          db.String(15),  nullable=True)
    direccion = db.Column(          db.Text,        nullable=True)
    estado    = db.Column('estatus',db.Boolean,     default=True)

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'
