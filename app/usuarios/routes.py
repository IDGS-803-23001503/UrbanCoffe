from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from model import Usuario, db

usuariosBp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def hayOtroGerenteActivo(idUsuarioActual: int) -> bool:
    return Usuario.query.filter(
        Usuario.id != idUsuarioActual,
        Usuario.rol == "Gerente",
        Usuario.estado == "Activo",
    ).first() is not None


def requiereRol(rolRequerido: str):
    def decorador(funcionVista):
        @wraps(funcionVista)
        def envuelta(*args, **kwargs):
            if not session.get("inicioSesion"):
                return redirect(url_for("auth.iniciarSesion"))

            if session.get("usuarioRol") != rolRequerido:
                flash("No tienes permisos para acceder a este módulo.", "danger")
                return redirect(url_for("dashboard_operador"))

            return funcionVista(*args, **kwargs)

        return envuelta

    return decorador


@usuariosBp.route("/", methods=["GET"], endpoint="index")
@requiereRol("Gerente")
def index():
    terminoBusqueda = request.args.get("q", "").strip()

    consultaUsuarios = Usuario.query
    if terminoBusqueda:
        patronBusqueda = f"%{terminoBusqueda}%"
        consultaUsuarios = consultaUsuarios.filter(
            or_(
                Usuario.nombre.ilike(patronBusqueda),
                Usuario.usuario.ilike(patronBusqueda),
                Usuario.correo.ilike(patronBusqueda),
                Usuario.rol.ilike(patronBusqueda),
                Usuario.estado.ilike(patronBusqueda),
            )
        )

    listaUsuarios = consultaUsuarios.order_by(Usuario.creadoEn.desc()).all()
    return render_template(
        "usuarios/usuarios.html",
        usuarios=listaUsuarios,
        terminoBusqueda=terminoBusqueda,
    )


@usuariosBp.route("/nuevo", methods=["GET"], endpoint="nuevo")
@requiereRol("Gerente")
def nuevo():
    return render_template("usuarios/nuevo_usuario.html")


@usuariosBp.route("/crear", methods=["POST"], endpoint="crear")
@requiereRol("Gerente")
def crear():
    nombre = request.form.get("nombre", "").strip()
    usuarioLogin = request.form.get("usuario", "").strip().lower()
    correo = request.form.get("correo", "").strip().lower()
    rol = request.form.get("rol", "").strip()
    contrasenaTemporal = request.form.get("contrasenaTemporal", "")
    estado = request.form.get("estado", "").strip()

    if not nombre or not usuarioLogin or not correo or rol not in {"Gerente", "Operador", "Cliente"} or not contrasenaTemporal or estado not in {"Activo", "Inactivo"}:
        flash("Completa todos los campos requeridos correctamente.", "danger")
        return redirect(url_for("usuarios.nuevo"))

    existeUsuario = Usuario.query.filter_by(usuario=usuarioLogin).first()
    if existeUsuario:
        flash("El usuario ya está registrado.", "danger")
        return redirect(url_for("usuarios.nuevo"))

    existe = Usuario.query.filter_by(correo=correo).first()
    if existe:
        flash("El correo ya está registrado.", "danger")
        return redirect(url_for("usuarios.nuevo"))

    usuario = Usuario(nombre=nombre, usuario=usuarioLogin, correo=correo, rol=rol, estado=estado)

    usuario.establecerContrasena(contrasenaTemporal)
    usuario.resetearSeguridad()

    db.session.add(usuario)
    db.session.commit()

    flash("Usuario creado correctamente.", "success")
    return redirect(url_for("usuarios.index"))


@usuariosBp.route("/<int:idUsuario>/editar", methods=["GET"], endpoint="editar")
@requiereRol("Gerente")
def editar(idUsuario: int):
    usuario = Usuario.query.get_or_404(idUsuario)
    return render_template("usuarios/editar_usuario.html", usuario=usuario)


@usuariosBp.route("/<int:idUsuario>/actualizar", methods=["POST"], endpoint="actualizar")
@requiereRol("Gerente")
def actualizar(idUsuario: int):
    usuario = Usuario.query.get_or_404(idUsuario)

    nombre = request.form.get("nombre", "").strip()
    usuarioLogin = request.form.get("usuario", "").strip().lower()
    correo = request.form.get("correo", "").strip().lower()
    rol = request.form.get("rol", "").strip()
    estado = request.form.get("estado", "").strip()
    contrasenaTemporal = request.form.get("contrasenaTemporal", "")

    if not nombre or not usuarioLogin or not correo or rol not in {"Gerente", "Operador", "Cliente"} or estado not in {"Activo", "Inactivo"}:
        flash("Completa todos los campos requeridos correctamente.", "danger")
        return redirect(url_for("usuarios.editar", idUsuario=idUsuario))

    usuarioRepetido = Usuario.query.filter(Usuario.usuario == usuarioLogin, Usuario.id != idUsuario).first()
    if usuarioRepetido:
        flash("El usuario ya está registrado por otra cuenta.", "danger")
        return redirect(url_for("usuarios.editar", idUsuario=idUsuario))

    correoRepetido = Usuario.query.filter(Usuario.correo == correo, Usuario.id != idUsuario).first()
    if correoRepetido:
        flash("El correo ya está registrado por otro usuario.", "danger")
        return redirect(url_for("usuarios.editar", idUsuario=idUsuario))

    perderaPrivilegiosGerente = usuario.rol == "Gerente" and (rol != "Gerente" or estado != "Activo")
    if perderaPrivilegiosGerente and not hayOtroGerenteActivo(idUsuario):
        flash("Debe existir al menos un Gerente activo en el sistema.", "danger")
        return redirect(url_for("usuarios.editar", idUsuario=idUsuario))

    usuario.nombre = nombre
    usuario.usuario = usuarioLogin
    usuario.correo = correo
    usuario.rol = rol
    usuario.estado = estado

    if contrasenaTemporal:
        usuario.establecerContrasena(contrasenaTemporal)
        usuario.resetearSeguridad()

    db.session.commit()
    flash("Usuario actualizado correctamente.", "success")
    return redirect(url_for("usuarios.index"))


@usuariosBp.route("/<int:idUsuario>/desactivar", methods=["POST"], endpoint="desactivar")
@requiereRol("Gerente")
def desactivar(idUsuario: int):
    usuario = Usuario.query.get_or_404(idUsuario)

    if usuario.id == session.get("usuarioId"):
        flash("No puedes desactivar tu propia cuenta.", "danger")
        return redirect(url_for("usuarios.index"))

    if usuario.rol == "Gerente" and not hayOtroGerenteActivo(idUsuario):
        flash("Debe existir al menos un Gerente activo en el sistema.", "danger")
        return redirect(url_for("usuarios.index"))

    usuario.estado = "Inactivo"
    usuario.resetearSeguridad()
    db.session.commit()

    flash("Usuario desactivado correctamente.", "success")
    return redirect(url_for("usuarios.index"))