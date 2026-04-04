
from flask_wtf import FlaskForm
from wtforms import StringField, DateTimeLocalField, TextAreaField, SubmitField, SelectField, IntegerField, RadioField
from wtforms.validators import DataRequired, Length, ValidationError
from datetime import datetime
from wtforms.validators import DataRequired, Optional
class PedidoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    telefono = StringField('Teléfono', validators=[Length(max=15)])

    hora_recogida = DateTimeLocalField(
        'Hora de recogida',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )

    notas = TextAreaField('Notas', validators=[Length(max=200)])

    submit = SubmitField('Crear Pedido')

    def validate_hora_recogida(self, field):
        ahora = datetime.now()
        diferencia = (field.data - ahora).total_seconds() / 60

        if field.data.date() != ahora.date():
            raise ValidationError("El pedido debe ser para hoy.")

        if diferencia < 10:
            raise ValidationError("Debe pedir con al menos 10 minutos de anticipación.")

        if diferencia > 60:
            raise ValidationError("No puedes pedir con más de 1 hora de anticipación.")

class VentaForm(FlaskForm):

 
    producto = SelectField("Producto", coerce=int, validators=[Optional()])

    cantidad = IntegerField("Cantidad", default=1, validators=[DataRequired()])

    tipo_venta = RadioField("Tipo", choices=[
        ("fisica", "Física"),
        ("en_linea", "En línea")
    ], validators=[Optional()])


    metodo_pago = SelectField("Método de pago", choices=[
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
        ("transferencia", "Transferencia")
    ], validators=[Optional()])

  
    hora_recogida = DateTimeLocalField(
        "Hora recogida",
        format='%Y-%m-%dT%H:%M',
        validators=[Optional()]
    )

    notas = StringField("Notas", validators=[Optional()])

    agregar = SubmitField("Agregar producto")
    terminar = SubmitField("Finalizar venta")


class PagoForm(FlaskForm):
    metodo_pago = SelectField("Método de Pago", choices=[
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia')
    ], validators=[DataRequired()])
    
    submit = SubmitField("Registrar Pago")
class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=50)])
    apellidoPaterno = StringField('Apellido Paterno', validators=[DataRequired(), Length(max=50)])
    apellidoMaterno = StringField('Apellido Materno', validators=[Optional(), Length(max=50)])
    telefono = StringField('Teléfono', validators=[DataRequired(), Length(max=15)])
    alias = StringField('Alias / Apodo', validators=[DataRequired(), Length(max=50)])
    estado = SelectField('Estado', choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], validators=[DataRequired()])
    
    # Campos para el usuario vinculado
    correo = StringField('Correo Electrónico', validators=[Optional(), Length(max=120)])
    contrasena = StringField('Contraseña', validators=[Optional()])
    
    submit = SubmitField('Guardar Cliente')