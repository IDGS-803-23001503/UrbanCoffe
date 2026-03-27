from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class MateriaPrima(db.Model):
    __tablename__ = 'Materia_prima' 

    id_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    # Temporalmente lo tratamos como entero normal, más adelante podemos hacer la relación con Unidad_medida
    unidad_medida = db.Column(db.Integer, nullable=False) 
    stock_minimo = db.Column(db.Numeric(10, 2), default=0.00)
    stock_actual = db.Column(db.Numeric(10, 2), default=0.00)