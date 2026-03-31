from datetime import datetime, timedelta, timezone
from decimal import Decimal

from flask import Flask, abort, redirect, render_template, request, session, url_for
from sqlalchemy import func
from sqlalchemy.exc import OperationalError

from config import Config
from app.login.routes import authBp, endpointDashboardRol, iniciarModuloAuth, usuarioAutenticado
from app.usuarios.routes import usuariosBp
from model import DetalleVenta, MateriaPrima, ProductoTerminado, Usuario, Venta, db

app = Flask(__name__)
app.config.from_object(Config)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

db.init_app(app)
app.register_blueprint(authBp)
app.register_blueprint(usuariosBp)
try:
    iniciarModuloAuth(app)
except OperationalError as exc:
    raise RuntimeError(
        "No fue posible conectar a MySQL."
    ) from exc


def sembrarDatosDashboard() -> None:
    if ProductoTerminado.query.count() == 0:
        db.session.add_all(
            [
                ProductoTerminado(nombre="Latte 12oz", precio=Decimal("59.00"), stockActual=45, stockMinimo=12, activo=True),
                ProductoTerminado(nombre="Americano 12oz", precio=Decimal("45.00"), stockActual=60, stockMinimo=15, activo=True),
                ProductoTerminado(nombre="Capuccino 12oz", precio=Decimal("57.00"), stockActual=35, stockMinimo=10, activo=True),
                ProductoTerminado(nombre="Moka 12oz", precio=Decimal("63.00"), stockActual=22, stockMinimo=8, activo=True),
            ]
        )
        db.session.commit()

    if MateriaPrima.query.count() == 0:
        db.session.add_all(
            [
                MateriaPrima(nombre="Café molido", unidadMedida="kg", stockActual=Decimal("3.50"), stockMinimo=Decimal("4.00"), costoUnitario=Decimal("220.00"), activa=True),
                MateriaPrima(nombre="Leche", unidadMedida="L", stockActual=Decimal("8.00"), stockMinimo=Decimal("6.00"), costoUnitario=Decimal("26.00"), activa=True),
                MateriaPrima(nombre="Jarabe vainilla", unidadMedida="L", stockActual=Decimal("0.70"), stockMinimo=Decimal("1.00"), costoUnitario=Decimal("145.00"), activa=True),
                MateriaPrima(nombre="Vasos 12oz", unidadMedida="pza", stockActual=Decimal("120"), stockMinimo=Decimal("80"), costoUnitario=Decimal("1.50"), activa=True),
            ]
        )
        db.session.commit()

    if Venta.query.count() > 0:
        return

    usuario = Usuario.query.filter_by(rol="Gerente").first() or Usuario.query.first()
    productos = ProductoTerminado.query.filter_by(activo=True).order_by(ProductoTerminado.id.asc()).all()
    if not usuario or not productos:
        return

    hoyBase = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
    for indiceDia in range(14):
        fechaDia = hoyBase - timedelta(days=indiceDia)

        for ticket in range(2):
            venta = Venta(
                usuarioId=usuario.id,
                total=Decimal("0.00"),
                utilidadBruta=Decimal("0.00"),
                confirmada=True,
                origen="ONLINE" if (indiceDia + ticket) % 4 == 0 else "POS",
                creadoEn=fechaDia + timedelta(hours=ticket * 3),
            )
            db.session.add(venta)
            db.session.flush()

            productoPrincipal = productos[(indiceDia + ticket) % len(productos)]
            productoSecundario = productos[(indiceDia + ticket + 1) % len(productos)]

            items = [
                (productoPrincipal, (indiceDia % 3) + 1),
                (productoSecundario, 1),
            ]

            totalVenta = Decimal("0.00")
            utilidadVenta = Decimal("0.00")

            for producto, cantidad in items:
                precioUnitario = Decimal(str(producto.precio))
                costoUnitario = (precioUnitario * Decimal("0.58")).quantize(Decimal("0.01"))
                subtotal = (precioUnitario * Decimal(cantidad)).quantize(Decimal("0.01"))
                utilidadLinea = ((precioUnitario - costoUnitario) * Decimal(cantidad)).quantize(Decimal("0.01"))

                db.session.add(
                    DetalleVenta(
                        ventaId=venta.id,
                        productoId=producto.id,
                        cantidad=cantidad,
                        precioUnitario=precioUnitario,
                        costoUnitario=costoUnitario,
                        subtotal=subtotal,
                    )
                )

                totalVenta += subtotal
                utilidadVenta += utilidadLinea

            venta.total = totalVenta
            venta.utilidadBruta = utilidadVenta

    db.session.commit()


with app.app_context():
    sembrarDatosDashboard()


def construirContextoDashboard(periodoDias: int, puedeVerFinanzas: bool) -> dict:
    hoy = datetime.now(timezone.utc)
    inicioHoy = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    finHoy = inicioHoy + timedelta(days=1)

    inicioPeriodo = (inicioHoy - timedelta(days=periodoDias - 1)).date()
    finPeriodo = inicioHoy.date()

    totalVentasDia = Decimal("0.00")
    utilidadBrutaDia = Decimal("0.00")
    numeroTicketsDia = 0

    if puedeVerFinanzas:
        totalVentasDia = db.session.query(func.coalesce(func.sum(Venta.total), 0)).filter(
            Venta.confirmada.is_(True),
            Venta.creadoEn >= inicioHoy,
            Venta.creadoEn < finHoy,
        ).scalar() or Decimal("0.00")

        utilidadBrutaDia = db.session.query(func.coalesce(func.sum(Venta.utilidadBruta), 0)).filter(
            Venta.confirmada.is_(True),
            Venta.creadoEn >= inicioHoy,
            Venta.creadoEn < finHoy,
        ).scalar() or Decimal("0.00")

        numeroTicketsDia = db.session.query(func.count(Venta.id)).filter(
            Venta.confirmada.is_(True),
            Venta.creadoEn >= inicioHoy,
            Venta.creadoEn < finHoy,
        ).scalar() or 0

    ventasPeriodo = db.session.query(
        func.date(Venta.creadoEn).label("fecha"),
        func.coalesce(func.sum(Venta.total), 0).label("monto"),
    ).filter(
        Venta.confirmada.is_(True),
        func.date(Venta.creadoEn) >= inicioPeriodo,
        func.date(Venta.creadoEn) <= finPeriodo,
    ).group_by(
        func.date(Venta.creadoEn)
    ).all()

    mapaVentas = {str(fila.fecha): float(fila.monto or 0) for fila in ventasPeriodo}
    etiquetas = []
    puntos = []

    for paso in range(periodoDias):
        fecha = inicioPeriodo + timedelta(days=paso)
        clave = fecha.isoformat()
        etiquetas.append(fecha.strftime("%d/%m"))
        puntos.append(round(mapaVentas.get(clave, 0.0), 2))

    topProductos = db.session.query(
        ProductoTerminado.nombre,
        func.coalesce(func.sum(DetalleVenta.cantidad), 0).label("cantidad"),
    ).join(
        DetalleVenta, DetalleVenta.productoId == ProductoTerminado.id
    ).join(
        Venta, Venta.id == DetalleVenta.ventaId
    ).filter(
        Venta.confirmada.is_(True),
        func.date(Venta.creadoEn) >= inicioPeriodo,
        func.date(Venta.creadoEn) <= finPeriodo,
    ).group_by(
        ProductoTerminado.id,
        ProductoTerminado.nombre,
    ).order_by(
        func.sum(DetalleVenta.cantidad).desc()
    ).limit(5).all()

    ultimasOperaciones = Venta.query.filter_by(confirmada=True).order_by(Venta.creadoEn.desc()).limit(7).all()
    alertasInsumos = MateriaPrima.query.filter(
        MateriaPrima.activa.is_(True),
        MateriaPrima.stockActual <= MateriaPrima.stockMinimo,
    ).order_by(MateriaPrima.stockActual.asc()).all()

    return {
        "periodoSeleccionado": periodoDias,
        "totalVentasDia": float(totalVentasDia),
        "utilidadBrutaDia": float(utilidadBrutaDia),
        "numeroTicketsDia": int(numeroTicketsDia),
        "etiquetasGrafica": etiquetas,
        "puntosGrafica": puntos,
        "topProductos": topProductos,
        "ultimasOperaciones": ultimasOperaciones,
        "alertasInsumos": alertasInsumos,
        "puedeVerFinanzas": puedeVerFinanzas,
    }


@app.before_request
def requerirLogin():
    endpointsPublicos = {
        "auth.iniciarSesion",
        "auth.registrarUsuario",
        "auth.recuperarContrasena",
        "auth.resetearContrasena",
        "index",
        "static",
    }

    if request.endpoint in endpointsPublicos:
        return None

    if not usuarioAutenticado():
        return redirect(url_for("auth.iniciarSesion"))

    return None


@app.route("/")
def index():
    if usuarioAutenticado():
        endpointRol = endpointDashboardRol(session.get("usuarioRol", "Operador"))
        return redirect(url_for(endpointRol))
    return redirect(url_for("auth.iniciarSesion"))


@app.route("/dashboard/gerente")
def dashboard_gerente():
    if session.get("usuarioRol") != "Gerente":
        abort(403)
    periodo = request.args.get("periodo", "7")
    periodoDias = int(periodo) if periodo in {"7", "15", "30"} else 7
    contexto = construirContextoDashboard(periodoDias=periodoDias, puedeVerFinanzas=True)
    return render_template("dashboard/index.html", **contexto)


@app.route("/dashboard/operador")
def dashboard_operador():
    if session.get("usuarioRol") not in {"Gerente", "Operador"}:
        abort(403)
    periodo = request.args.get("periodo", "7")
    periodoDias = int(periodo) if periodo in {"7", "15", "30"} else 7
    contexto = construirContextoDashboard(periodoDias=periodoDias, puedeVerFinanzas=False)
    return render_template("dashboard/index.html", **contexto)


if __name__ == "__main__":
    app.run(debug=True)