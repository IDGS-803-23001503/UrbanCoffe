from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


ROLES_USUARIO = [
    ("Gerente", "Gerente"),
    ("Operador", "Operador"),
    ("Cliente", "Cliente"),
]

ESTADOS_USUARIO = [
    ("Activo", "Activo"),
    ("Inactivo", "Inactivo"),
]


class LoginForm(FlaskForm):
    correo = StringField(
        "Correo o Usuario",
        validators=[
            DataRequired(message="El correo o usuario es obligatorio"),
            Length(max=120, message="El identificador no puede exceder 120 caracteres"),
        ],
    )
    contrasena = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="La contraseña es obligatoria"),
            Length(min=6, max=128, message="La contraseña debe tener entre 6 y 128 caracteres"),
        ],
    )


class RegistroUsuarioForm(FlaskForm):
    nombre = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre es obligatorio"),
            Length(min=3, max=120, message="El nombre debe tener entre 3 y 120 caracteres"),
        ],
    )
    correo = StringField(
        "Correo Electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio"),
            Email(message="Ingrese un correo válido"),
            Length(max=120, message="El correo no puede exceder 120 caracteres"),
        ],
    )
    contrasena = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="La contraseña es obligatoria"),
            Length(min=6, max=128, message="La contraseña debe tener entre 6 y 128 caracteres"),
        ],
    )


class RecuperarContrasenaForm(FlaskForm):
    correo = StringField(
        "Correo Electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio"),
            Email(message="Ingrese un correo válido"),
            Length(max=120, message="El correo no puede exceder 120 caracteres"),
        ],
    )


class ResetearContrasenaForm(FlaskForm):
    contrasena = PasswordField(
        "Nueva Contraseña",
        validators=[
            DataRequired(message="La nueva contraseña es obligatoria"),
            Length(min=8, max=128, message="La contraseña debe tener entre 8 y 128 caracteres"),
        ],
    )
    confirmarContrasena = PasswordField(
        "Confirmar Contraseña",
        validators=[
            DataRequired(message="Debes confirmar la contraseña"),
            EqualTo("contrasena", message="Las contraseñas no coinciden"),
        ],
    )


class UsuarioCrearForm(FlaskForm):
    nombre = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre es obligatorio"),
            Length(min=3, max=120, message="El nombre debe tener entre 3 y 120 caracteres"),
        ],
    )
    usuario = StringField(
        "Usuario",
        validators=[
            DataRequired(message="El usuario es obligatorio"),
            Length(min=3, max=60, message="El usuario debe tener entre 3 y 60 caracteres"),
        ],
    )
    correo = StringField(
        "Correo Electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio"),
            Email(message="Ingrese un correo válido"),
            Length(max=120, message="El correo no puede exceder 120 caracteres"),
        ],
    )
    rol = SelectField(
        "Rol",
        choices=ROLES_USUARIO,
        validators=[DataRequired(message="El rol es obligatorio")],
    )
    contrasenaTemporal = PasswordField(
        "Contraseña Temporal",
        validators=[
            DataRequired(message="La contraseña temporal es obligatoria"),
            Length(min=6, max=128, message="La contraseña debe tener entre 6 y 128 caracteres"),
        ],
    )
    estado = SelectField(
        "Estado",
        choices=ESTADOS_USUARIO,
        validators=[DataRequired(message="El estado es obligatorio")],
    )


class UsuarioActualizarForm(FlaskForm):
    nombre = StringField(
        "Nombre",
        validators=[
            DataRequired(message="El nombre es obligatorio"),
            Length(min=3, max=120, message="El nombre debe tener entre 3 y 120 caracteres"),
        ],
    )
    usuario = StringField(
        "Usuario",
        validators=[
            DataRequired(message="El usuario es obligatorio"),
            Length(min=3, max=60, message="El usuario debe tener entre 3 y 60 caracteres"),
        ],
    )
    correo = StringField(
        "Correo Electrónico",
        validators=[
            DataRequired(message="El correo es obligatorio"),
            Email(message="Ingrese un correo válido"),
            Length(max=120, message="El correo no puede exceder 120 caracteres"),
        ],
    )
    rol = SelectField(
        "Rol",
        choices=ROLES_USUARIO,
        validators=[DataRequired(message="El rol es obligatorio")],
    )
    contrasenaTemporal = PasswordField(
        "Contraseña Temporal",
        validators=[
            Optional(),
            Length(min=6, max=128, message="La contraseña debe tener entre 6 y 128 caracteres"),
        ],
    )
    estado = SelectField(
        "Estado",
        choices=ESTADOS_USUARIO,
        validators=[DataRequired(message="El estado es obligatorio")],
    )
