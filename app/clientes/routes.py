from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from model import Cliente, Usuario, db
from forms import ClienteForm 

clientesBp = Blueprint("clientes", __name__, url_prefix="/clientes")


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


# 📋 LISTAR CLIENTES
@clientesBp.route("/", methods=["GET"], endpoint="index")
@requiereRol("Gerente")
def index():
    clientes = Cliente.query.order_by(Cliente.creadoEn.desc()).all()
    return render_template("clientes/clientes.html", clientes=clientes)


# ➕ FORMULARIO NUEVO
@clientesBp.route("/nuevo", methods=["GET"], endpoint="nuevo")
@requiereRol("Gerente")
def nuevo():
    # 1. Instancia el formulario
    form = ClienteForm() 
    # 2. Pásalo a la plantilla usando form=form
    return render_template("clientes/nuevo_cliente.html", form=form)


@clientesBp.route("/crear", methods=["POST"], endpoint="crear")
@requiereRol("Gerente")
def crear():
    form = ClienteForm()
    if form.validate_on_submit():
        # Validar si el correo ya existe
        if Usuario.query.filter_by(correo=form.correo.data).first():
            flash("El correo ya está registrado.", "danger")
            return redirect(url_for("clientes.nuevo"))

        try:
            # 1. Crear Usuario
            nuevo_usuario = Usuario(
                nombre=f"{form.nombre.data} {form.apellidoPaterno.data}",
                correo=form.correo.data.lower(),
                rol="Cliente",
                estado=form.estado.data
            )
            nuevo_usuario.establecerContrasena(form.contrasena.data)
            db.session.add(nuevo_usuario)
            db.session.flush()

            # 2. Crear Cliente
            nuevo_cliente = Cliente(
                nombre=form.nombre.data,
                apellidoPaterno=form.apellidoPaterno.data,
                apellidoMaterno=form.apellidoMaterno.data,
                telefono=form.telefono.data,
                alias=form.alias.data,
                estado=form.estado.data,
                usuarioId=nuevo_usuario.id
            )
            db.session.add(nuevo_cliente)
            db.session.commit()
            flash("Cliente y usuario creados correctamente.", "success")
            return redirect(url_for("clientes.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")
    
    return render_template("clientes/nuevo_cliente.html", form=form)


# ✏️ EDITAR
@clientesBp.route("/<int:idCliente>/editar", methods=["GET"], endpoint="editar")
@requiereRol("Gerente")
def editar(idCliente):
    cliente = Cliente.query.get_or_404(idCliente)
    # Rellenamos el form con el objeto cliente
    form = ClienteForm(obj=cliente) 
    return render_template("clientes/nuevo_cliente.html", cliente=cliente, form=form)



@clientesBp.route("/<int:idCliente>/actualizar", methods=["POST"], endpoint="actualizar")
@requiereRol("Gerente")
def actualizar(idCliente):
    cliente = Cliente.query.get_or_404(idCliente)

    nombre = request.form.get("nombre", "").strip()
    telefono = request.form.get("telefono", "").strip()
    alias = request.form.get("alias", "").strip()
    estado = request.form.get("estado", "").strip()

    if not nombre or estado not in {"Activo", "Inactivo"}:
        flash("Datos inválidos.", "danger")
        return redirect(url_for("clientes.editar", idCliente=idCliente))

    cliente.nombre = nombre
    cliente.telefono = telefono if telefono else None
    cliente.alias = alias if alias else None
    cliente.estado = estado

    db.session.commit()

    flash("Cliente actualizado correctamente.", "success")
    return redirect(url_for("clientes.index"))



@clientesBp.route("/<int:idCliente>/desactivar", methods=["POST"], endpoint="desactivar")
@requiereRol("Gerente")
def desactivar(idCliente):
    cliente = Cliente.query.get_or_404(idCliente)

    cliente.estado = "Inactivo"

    db.session.commit()

    flash("Cliente desactivado correctamente.", "success")
    return redirect(url_for("clientes.index"))