from functools import wraps
from flask import Blueprint, flash, redirect, render_template, session, url_for, request
from model import db, Producto
from forms import VentaForm, PagoForm
from sqlalchemy import text, exc
from datetime import datetime, timedelta
import csv
from io import StringIO
from flask import make_response

from flask import request

ventasBp = Blueprint("ventas", __name__, url_prefix="/ventas")



def requiereRol(rolRequerido: str):
    def decorador(funcionVista):
        @wraps(funcionVista)
        def envuelta(*args, **kwargs):
            if not session.get("inicioSesion"):
                return redirect(url_for("auth.iniciarSesion"))

            if session.get("usuarioRol") != rolRequerido:
                flash("No tienes permisos.", "danger")
                return redirect(url_for("dashboard_operador"))

            return funcionVista(*args, **kwargs)
        return envuelta
    return decorador


@ventasBp.route("/", methods=["GET"], endpoint="index")
@requiereRol("Gerente")
def index():
    # Obtener fecha del filtro o usar la actual
    fecha_filtro = request.args.get('fecha')
    if not fecha_filtro:
        fecha_filtro = datetime.now().strftime('%Y-%m-%d')

    # Consulta filtrada por fecha (solo la parte de la fecha del DATETIME)
    query = text("""
        SELECT * FROM Ventas 
        WHERE DATE(fecha) = :f 
        ORDER BY fecha DESC
    """)
    ventas = db.session.execute(query, {"f": fecha_filtro}).fetchall()

    # Calcular totales específicos para las tarjetas de resumen
    total_efectivo = sum(v.total for v in ventas if v.metodo_pago == 'Efectivo')
    total_tarjeta = sum(v.total for v in ventas if v.metodo_pago == 'Tarjeta')
    total_dia = total_efectivo + total_tarjeta
    num_transacciones = len(ventas)

    return render_template(
        "ventas/ventas.html", 
        ventas=ventas, 
        fecha_actual=fecha_filtro,
        total_efectivo=total_efectivo,
        total_tarjeta=total_tarjeta,
        total_dia=total_dia,
        transacciones=num_transacciones
    )
@ventasBp.route("/reporte", methods=["GET"])
@requiereRol("Gerente")
def generar_reporte():
    fecha_filtro = request.args.get('fecha')
    if not fecha_filtro:
        fecha_filtro = datetime.now().strftime('%Y-%m-%d')

    # 1. Obtener los datos de la base de datos
    query = text("""
        SELECT v.id_venta, v.fecha, v.metodo_pago, v.total, u.nombre as usuario
        FROM Ventas v
        JOIN Usuarios u ON v.id_usuario = u.id 
        WHERE DATE(v.fecha) = :f
    """)
    ventas = db.session.execute(query, {"f": fecha_filtro}).fetchall()

    # 2. Crear el archivo CSV en memoria
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Folio', 'Fecha/Hora', 'Metodo Pago', 'Total', 'Atendio']) # Encabezados
    
    total_acumulado = 0
    for v in ventas:
        cw.writerow([f"UC-{v.id_venta}", v.fecha, v.metodo_pago, v.total, v.usuario])
        total_acumulado += v.total
    
    cw.writerow([])
    cw.writerow(['', '', 'TOTAL DEL DIA:', total_acumulado])

    # 3. Configurar la respuesta del navegador para descarga
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=Reporte_{fecha_filtro}.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output
@ventasBp.route("/fisica", methods=["GET", "POST"], endpoint="fisica")
@requiereRol("Operador")
def venta_fisica():
    form = VentaForm()
    productos = Producto.query.filter_by(estado=True).all()
    
    if request.method == "POST":
        
        if "agregar" in request.form:
            p_id = request.form.get("producto_id", type=int)
            prod = Producto.query.get(p_id)
            if prod:
                carrito = session.get("carrito", [])
                carrito.append({
                    "id_producto": p_id,
                    "nombre": prod.nombre,
                    "precio": float(prod.precio),
                    "cantidad": 1
                })
                session["carrito"] = carrito
                session.modified = True
            return redirect(url_for("ventas.fisica"))

        
        if "quitar" in request.form:
            idx = request.form.get("item_index", type=int)
            carrito = session.get("carrito", [])
            if 0 <= idx < len(carrito):
                carrito.pop(idx)
                session["carrito"] = carrito
                session.modified = True
            return redirect(url_for("ventas.fisica"))

        # --- 3. TERMINAR (Versión Anti-Duplicados) ---
        if "terminar" in request.form:
            carrito = session.get("carrito", [])
            if not carrito: 
                return redirect(url_for("ventas.fisica"))
            
            try:
                id_venta_actual = 0
                for item in carrito:
                    # Usamos parámetros limpios
                    result = db.session.execute(
                        text("CALL crear_venta_general(:u, :c, :tipo, :p, :can, :v_id)"),
                        {
                            "u": session.get("usuarioId"),
                            "c": None,
                            "tipo": "fisica",
                            "p": item["id_producto"],
                            "can": item["cantidad"],
                            "v_id": id_venta_actual
                        }
                    )
                    row = result.fetchone()
                    if row:
                        id_venta_actual = row[0]

                db.session.commit()
                
                # 1. Borramos el contenido del carrito
                session["carrito"] = [] 
                # 2. Eliminamos la llave por completo
                session.pop("carrito", None) 
                # 3. Forzamos a Flask a guardar este cambio de sesión AHORA
                session.modified = True 
                
                return redirect(url_for("ventas.form_pagar", idVenta=id_venta_actual))
                
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {str(e)}", "danger")
                return redirect(url_for("ventas.fisica"))

    carrito = session.get("carrito", [])
    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    return render_template("ventas/fisica.html", form=form, productos=productos, carrito=carrito, total=total)
@ventasBp.route("/<int:idVenta>/pagar", methods=["GET", "POST"])
@requiereRol("Operador") # Protegemos toda la transacción
def pagar_venta_gestion(idVenta): # Cambiamos el nombre para que sea único
    form = PagoForm()
    
    # 1. Si es GET: Mostramos el formulario de cobro
    if request.method == "GET":
        try:
            # IMPORTANTE: "ventas" en minúscula como en tu PROCEDURE
            result = db.session.execute(
                text("SELECT total FROM ventas WHERE id_venta = :id"), 
                {"id": idVenta}
            ).fetchone()
            
            if not result:
                flash("La venta no existe", "warning")
                return redirect(url_for("ventas.fisica"))
            
            return render_template("ventas/pagar.html", 
                                 form=form, 
                                 idVenta=idVenta, 
                                 total=result[0])
        except Exception as e:
            print(f"Error GET pagar: {e}")
            return redirect(url_for("ventas.fisica"))

    # 2. Si es POST: Procesamos el pago (Cuando dan clic en Efectivo/Tarjeta)
    metodo = request.form.get("metodo_pago")
    # notas = request.form.get("notas") # Por si lo necesitas luego
    
    try:
        # Ejecutamos el procedimiento que ya corregimos
        db.session.execute(
            text("CALL pagar_venta(:id, :met)"), 
            {"id": idVenta, "met": metodo}
        )
        db.session.commit()
        
        flash(f"¡Venta #{idVenta} pagada con éxito!", "success")
        return redirect(url_for("ventas.ticket", idVenta=idVenta))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar el pago: {str(e)}", "danger")
        return redirect(url_for("ventas.fisica"))
##       ----------   ESTA RUTA ES PARA PROBAR SIN RESTRICCIONES DE HORARIOS ------------------------
# @ventasBp.route("/online", methods=["GET", "POST"], endpoint="online")
# @requiereRol("Cliente")
# def venta_online():
#     form = VentaForm()
#     
#     # Consulta de productos
#     query_productos = text("""
#         SELECT p.*, 
#         CASE 
#             WHEN EXISTS (
#                 SELECT 1 FROM Recetas r 
#                 JOIN Materia_prima mp ON r.id_materia = mp.id_materia 
#                 WHERE r.id_producto = p.id_producto AND mp.stock_actual < r.cantidad
#             ) THEN 0 ELSE 1 
#         END as disponible_stock
#         FROM Producto p WHERE p.estatus = 1
#     """)
#     productos = db.session.execute(query_productos).fetchall()
# 
#     if request.method == "POST":
#         # --- QUITAR DEL CARRITO ---
#         if "quitar" in request.form:
#             index = request.form.get("item_index", type=int)
#             carrito = session.get("carrito", [])
#             if 0 <= index < len(carrito):
#                 carrito.pop(index)
#                 session["carrito"] = carrito
#                 session.modified = True
#             return redirect(url_for("ventas.online"))
# 
#         # --- AGREGAR AL CARRITO ---
#         if "agregar" in request.form:
#             prod_id = request.form.get("producto")
#             cant = request.form.get("cantidad", type=int, default=1)
#             nombre = request.form.get("nombre_prod")
#             prod_actual = next((p for p in productos if str(p.id_producto) == prod_id), None)
#             
#             if prod_actual and prod_actual.disponible_stock == 0:
#                 flash(f"Agotado: {nombre}", "danger")
#                 return redirect(url_for("ventas.online"))
# 
#             carrito = session.get("carrito", [])
#             carrito.append({
#                 "id_producto": int(prod_id), 
#                 "cantidad": cant, 
#                 "nombre": nombre,
#                 "precio": float(prod_actual.precio_venta) if prod_actual else 0 
#             })
#             session["carrito"] = carrito
#             session.modified = True
#             flash(f"¡{nombre} añadido!", "success")
#             return redirect(url_for("ventas.online"))
# 
#         # --- FINALIZAR PEDIDO (MODO PRUEBA) ---
#         if "terminar" in request.form:
#             carrito = session.get("carrito", [])
#             if not carrito:
#                 flash("Carrito vacío", "warning")
#                 return redirect(url_for("ventas.online"))
# 
#             hora_recogida_raw = request.form.get("hora_recogida")
#             u_id = session.get("usuarioId")
#             c_id = session.get("clienteId")
# 
#             id_venta_tracker = 0 
#             try:
#                 for item in carrito:
#                     result = db.session.execute(
#                         text("CALL crear_venta_online(:u, :c, :h, :n, :p, :can, :v_ex)"),
#                         {
#                             "u": u_id, "c": c_id, "h": hora_recogida_raw, 
#                             "n": request.form.get("notas", ""),
#                             "p": item["id_producto"], "can": item["cantidad"], 
#                             "v_ex": id_venta_tracker
#                         }
#                     ).fetchone()
#                     if result: id_venta_tracker = result[0]
#                 
#                 db.session.commit()
#                 session.pop("carrito", None)
#                 flash("¡Pedido confirmado!", "success")
#             except Exception as e:
#                 db.session.rollback()
#                 # Esto te dirá el error real que escupe la base de datos
#                 flash(f"Error: {str(e)}", "danger")
#             
#             return redirect(url_for("ventas.online"))
# 
#     return render_template("ventas/online.html", form=form, lista_productos=productos)
 

@ventasBp.route("/online", methods=["GET", "POST"], endpoint="online")
@requiereRol("Cliente")
def venta_online():
    form = VentaForm()
    
    # CONSULTA MAESTRA: Verifica disponibilidad basada en materia prima
    query_productos = text("""
        SELECT p.*, 
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM Recetas r 
                JOIN Materia_prima mp ON r.id_materia = mp.id_materia 
                WHERE r.id_producto = p.id_producto AND mp.stock_actual < r.cantidad
            ) THEN 0 ELSE 1 
        END as disponible_stock
        FROM Producto p WHERE p.estatus = 1
    """)
    productos = db.session.execute(query_productos).fetchall()

    if request.method == "POST":
        # --- QUITAR DEL CARRITO ---
        if "quitar" in request.form:
            index = request.form.get("item_index", type=int)
            carrito = session.get("carrito", [])
            if 0 <= index < len(carrito):
                eliminado = carrito.pop(index)
                session["carrito"] = carrito
                session.modified = True
                flash(f"Se quitó {eliminado['nombre']} del pedido", "info")
            return redirect(url_for("ventas.online"))

        # --- AGREGAR AL CARRITO ---
        if "agregar" in request.form:
            prod_id = request.form.get("producto")
            cant = request.form.get("cantidad", type=int, default=1)
            nombre = request.form.get("nombre_prod")
            
            prod_actual = next((p for p in productos if str(p.id_producto) == prod_id), None)
            
            if prod_actual and prod_actual.disponible_stock == 0:
                flash(f"Lo sentimos, {nombre} se ha agotado.", "danger")
                return redirect(url_for("ventas.online"))

            precio = float(prod_actual.precio_venta) if prod_actual else 0

            carrito = session.get("carrito", [])
            carrito.append({
                "id_producto": int(prod_id), 
                "cantidad": cant, 
                "nombre": nombre,
                "precio": precio 
            })
            session["carrito"] = carrito
            session.modified = True
            flash(f"¡{nombre} añadido con éxito!", "success")
            return redirect(url_for("ventas.online"))

        # --- FINALIZAR PEDIDO ---
        if "terminar" in request.form:
            carrito = session.get("carrito", [])
            if not carrito:
                flash("Carrito vacío", "warning")
                return redirect(url_for("ventas.online"))

            hora_recogida_raw = request.form.get("hora_recogida")
            
            try:
                hora_pedido = datetime.strptime(hora_recogida_raw, '%Y-%m-%dT%H:%M')
                ahora = datetime.now()
                
                # 1. Validar horario de cierre
                if hora_pedido.hour >= 24 or (hora_pedido.hour >= 23 and hora_pedido.minute > 59):
                    flash("Lo sentimos, la sucursal va a cerrar o ya está cerrada. Te sugerimos realizar tu pedido para el día de mañana.", "warning")
                    return redirect(url_for("ventas.online"))

                # 2. Validar anticipación (30 min con 5 de gracia)
                if hora_pedido < (ahora + timedelta(minutes=25)):
                    flash("Requerimos al menos 30 minutos de anticipación para preparar tus productos con calidad.", "danger")
                    return redirect(url_for("ventas.online"))

            except ValueError:
                flash("Formato de hora inválido.", "danger")
                return redirect(url_for("ventas.online"))

            try:
                hora_pedido = datetime.strptime(hora_recogida_raw, '%Y-%m-%dT%H:%M')
                ahora = datetime.now()
                
                # Validación: Solo hoy
                if hora_pedido.date() != ahora.date():
                    flash("Los pedidos online solo se pueden realizar para el día de hoy.", "danger")
                    return redirect(url_for("ventas.online"))
                
                # Validación: 2 horas de anticipación (según tu segunda lógica)
                if hora_pedido < (ahora + timedelta(hours=2)):
                    flash("Para preparar tu pedido con calidad, requerimos al menos 1 hora de anticipación.", "danger")
                    return redirect(url_for("ventas.online"))

            except ValueError:
                flash("El formato de fecha y hora no es correcto.", "danger")
                return redirect(url_for("ventas.online"))
            
            # 2. VALIDACIÓN DE SESIÓN
            u_id = session.get("usuarioId")
            c_id = session.get("clienteId")

            if u_id is None:
                flash("Tu sesión ha expirado. Por favor, vuelve a ingresar.", "danger")
                return redirect(url_for("auth.iniciarSesion"))

            id_venta_tracker = 0 
            
            try:
                for item in carrito:
                    result = db.session.execute(
                        text("CALL crear_venta_online(:u, :c, :h, :n, :p, :can, :v_ex)"),
                        {
                            "u": u_id, "c": c_id, 
                            "h": hora_recogida_raw, 
                            "n": request.form.get("notas", ""),
                            "p": item["id_producto"], "can": item["cantidad"], 
                            "v_ex": id_venta_tracker
                        }
                    ).fetchone()
                    
                    if result:
                        id_venta_tracker = result[0]
                
                db.session.commit()
                session.pop("carrito", None)
                flash("¡Pedido confirmado! Te esperamos a la hora indicada.", "success")
                return redirect(url_for("ventas.online"))

            except exc.IntegrityError:
                db.session.rollback()
                flash("Hubo un problema con tu cuenta de usuario. Contacta a soporte.", "danger")
            except exc.InternalError as e:
                db.session.rollback()
                error_msg = str(e.orig).split("'")[1] if "'" in str(e.orig) else "No hay stock suficiente para procesar la orden."
                flash(f"Aviso: {error_msg}", "warning")
            except Exception as e:
                db.session.rollback()
                flash("Lo sentimos, no pudimos procesar tu pedido en este momento.", "danger")
            
            return redirect(url_for("ventas.online"))

    return render_template("ventas/online.html", form=form, lista_productos=productos)

#  TICKET
@ventasBp.route("/ticket/<int:idVenta>", methods=["GET", "POST"], endpoint="ticket")
@requiereRol("Operador")
def ticket(idVenta):
    # USAMOS text() para envolver la consulta
    query = text("""
        SELECT 
            v.id_venta, v.fecha, v.metodo_pago, v.total,
            c.nombre AS cliente,
            p.nombre AS producto,
            dv.cantidad,
            dv.subtotal
        FROM Ventas v
        JOIN Detalle_venta dv ON v.id_venta = dv.id_venta
        JOIN Producto p ON dv.id_producto = p.id_producto
        LEFT JOIN Clientes c ON v.id_cliente = c.id_cliente
        WHERE v.id_venta = :idVenta
    """)
    
    # Ejecutamos pasando el objeto query
    resultado = db.session.execute(query, {"idVenta": idVenta}).fetchall()

    return render_template("ventas/ticket.html", ticket=resultado)