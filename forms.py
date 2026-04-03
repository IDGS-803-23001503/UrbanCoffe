from flask_wtf import FlaskForm
from wtforms import SelectField, DateField
from wtforms.validators import DataRequired, Optional


# ============================================
# FORMULARIOS PARA EL MÓDULO DE COMPRAS
# ============================================

class CompraForm(FlaskForm):
    """Formulario para registrar una nueva compra"""
    id_proveedor = SelectField('Proveedor', coerce=int, validators=[
        DataRequired(message='Debe seleccionar un proveedor')
    ])
    fecha = DateField('Fecha de Compra', format='%Y-%m-%d', validators=[
        DataRequired(message='La fecha es obligatoria')
    ])

    def __init__(self, *args, **kwargs):
        super(CompraForm, self).__init__(*args, **kwargs)
        from model import Proveedor
        self.id_proveedor.choices = [(0, 'Seleccione un proveedor')] + [
            (p.id_proveedor, p.nombre)
            for p in Proveedor.query.filter_by(estatus=True).all()
        ]


class FiltroComprasForm(FlaskForm):
    """Formulario para filtrar la lista de compras"""
    fecha_inicio = DateField('Fecha Inicio', format='%Y-%m-%d', validators=[Optional()])
    fecha_fin    = DateField('Fecha Fin',    format='%Y-%m-%d', validators=[Optional()])
    id_proveedor = SelectField('Proveedor', coerce=int, choices=[(0, 'Todos')])
    estatus      = SelectField('Estado', choices=[
        ('todos',      'Todos'),
        ('activas',    'Activas'),
        ('canceladas', 'Canceladas')
    ])

    def __init__(self, *args, **kwargs):
        super(FiltroComprasForm, self).__init__(*args, **kwargs)
        from model import Proveedor
        self.id_proveedor.choices = [(0, 'Todos')] + [
            (p.id_proveedor, p.nombre)
            for p in Proveedor.query.all()
        ]