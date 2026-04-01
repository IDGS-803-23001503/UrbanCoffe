from flask_wtf import FlaskForm
from wtforms import DateField
from wtforms.validators import DataRequired

# ============================================
# FORMULARIO COSTO Y UTILIDAD
# ============================================

class FechasReporteForm(FlaskForm):
    fecha_inicio = DateField('Fecha Inicio', format='%Y-%m-%d', validators=[
        DataRequired(message='La fecha de inicio es obligatoria')
    ])
    fecha_fin = DateField('Fecha Fin', format='%Y-%m-%d', validators=[
        DataRequired(message='La fecha de fin es obligatoria')
    ])