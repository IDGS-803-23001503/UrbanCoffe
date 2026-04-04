from functools import wraps
from flask import Blueprint, flash, redirect, render_template, session, url_for, request
from model import db, Producto
from forms import VentaForm, PagoForm
from sqlalchemy import text, exc

from flask import request # <--- ASEGÚRATE DE TENER ESTA IMPORTACIÓN


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
  
    ventas = db.session.execute(text("SELECT * FROM Ventas ORDER BY fecha DESC")).fetchall()
    return render_template("ventas/ventas.html", ventas=ventas)

@ventasBp.route("/fisica", methods=["GET", "POST"], endpoint="fisica")
@requiereRol("Operador")
def venta_fisica():
    form = VentaForm()
    productos = Producto.query.filter_by(estado=True).all()
    
    # IMPORTANTE: Aseguramos que el formulario tenga las opciones cargadas
    form.producto.choices = [(p.id_producto, p.nombre) for p in productos]

    if request.method == "POST":
        # --- 🛒 1. ACCIÓN: AGREGAR AL CARRITO ---
        if "agregar" in request.form:
            p_id = request.form.get("producto", type=int)
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

        # --- 🗑️ 2. ACCIÓN: QUITAR DEL CARRITO ---
        if "quitar" in request.form:
            idx = request.form.get("item_index", type=int)
            carrito = session.get("carrito", [])
            if 0 <= idx < len(carrito):
                carrito.pop(idx)
                session["carrito"] = carrito
                session.modified = True
            return redirect(url_for("ventas.fisica"))

        # --- 💰 3. ACCIÓN: CONFIRMAR Y PAGAR (CORREGIDA PARA INOUT) ---
        if "terminar" in request.form:
            carrito = session.get("carrito", [])
            if not carrito:
                return redirect(url_for("ventas.fisica"))
            
            id_venta_tracker = 0
            try:
                # 1. Inicializamos la variable en MySQL
                db.session.execute(text("SET @id_v = :inicio"), {"inicio": id_venta_tracker})

                for item in carrito:
                    # 2. Llamamos al procedimiento usando la variable @id_v de MySQL
                    db.session.execute(
                        text("""
                            CALL crear_venta_general(
                                :u, :c, :met, :tipo, :h, :n, :p, :can, @id_v
                            )
                        """),
                        {
                            "u": session.get("usuarioId"), 
                            "c": None, 
                            "met": "Efectivo", 
                            "tipo": "fisica", 
                            "h": None, 
                            "n": "Venta Mostrador",
                            "p": item["id_producto"], 
                            "can": item["cantidad"]
                        }
                    )
                
                # 3. Recuperamos el ID final que generó la base de datos
                res_id = db.session.execute(text("SELECT @id_v")).fetchone()
                id_venta_final = res_id[0] if res_id else 0

                db.session.commit()
                session.pop("carrito", None)
                
                # Si se generó una venta, vamos al ticket
                if id_venta_final > 0:
                    return redirect(url_for("ventas.ticket", idVenta=id_venta_final))
                else:
                    flash("Error al recuperar el ID de venta", "danger")
                    return redirect(url_for("ventas.fisica"))
                
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG ERROR: {str(e)}")
                flash(f"Error en la base de datos: {str(e)}", "danger")
                return redirect(url_for("ventas.fisica"))
                
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG ERROR: {str(e)}")
                flash(f"Error: {str(e)}", "danger")
                return redirect(url_for("ventas.fisica"))

    # Si es GET, solo mostramos la página
    return render_template("ventas/fisica.html", form=form, productos=productos)

@ventasBp.route("/<int:idVenta>/pagar", methods=["POST"], endpoint="pagar")
@requiereRol("Operador")
def pagar(idVenta):
    metodo = request.form.get("metodo_pago")
    try:
        # Llamamos al SP de pagar que actualiza el método de pago
        db.session.execute(text("CALL pagar_venta(:id, :met)"), {"id": idVenta, "met": metodo})
        db.session.commit()
        return redirect(url_for("ventas.ticket", idVenta=idVenta))
    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")
        return redirect(url_for("ventas.fisica"))

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
        # --- 🗑️ QUITAR DEL CARRITO ---
        if "quitar" in request.form:
            index = request.form.get("item_index", type=int)
            carrito = session.get("carrito", [])
            if 0 <= index < len(carrito):
                eliminado = carrito.pop(index)
                session["carrito"] = carrito
                session.modified = True
                flash(f"Se quitó {eliminado['nombre']}", "info")
            return redirect(url_for("ventas.online"))

        # --- 🛒 AGREGAR AL CARRITO ---
        if "agregar" in request.form:
            prod_id = request.form.get("producto")
            cant = request.form.get("cantidad", type=int, default=1)
            nombre = request.form.get("nombre_prod")
            
            # Buscar el precio en la lista de productos actual
            prod_actual = next((p for p in productos if str(p.id_producto) == prod_id), None)
            precio = float(prod_actual.precio_venta) if prod_actual else 0

            carrito = session.get("carrito", [])
            carrito.append({
                "id_producto": int(prod_id), 
                "cantidad": cant, 
                "nombre": nombre,
                "precio": precio # Guardamos el precio para el HTML
            })
            session["carrito"] = carrito
            session.modified = True
            flash(f"{nombre} agregado", "success")
            return redirect(url_for("ventas.online"))

        # --- 💰 FINALIZAR PEDIDO (Llamada al SP) ---
        if "terminar" in request.form:
            carrito = session.get("carrito", [])
            if not carrito:
                flash("El carrito está vacío", "danger")
                return redirect(url_for("ventas.online"))

            # 1. Validar que existan los IDs necesarios en la sesión
            u_id = session.get("usuarioId")
            c_id = session.get("clienteId")

            if u_id is None:
                # Si el usuarioId 3 no existe en la tabla 'usuario', este es el problema.
                flash("Error de sesión: No se encontró un ID de usuario válido. Reintenta iniciar sesión.", "danger")
                return redirect(url_for("auth.iniciarSesion"))

            id_venta_tracker = 0 
            
            try:
                for item in carrito:
                    # Ejecutamos el procedimiento
                    result = db.session.execute(
                        text("CALL crear_venta_online(:u, :c, :h, :n, :p, :can, :v_ex)"),
                        {
                            "u": u_id, 
                            "c": c_id, 
                            "h": request.form.get("hora_recogida"), 
                            "n": request.form.get("notas"),
                            "p": item["id_producto"], 
                            "can": item["cantidad"], 
                            "v_ex": id_venta_tracker
                        }
                    ).fetchone()
                    
                    if result:
                        id_venta_tracker = result[0]
                
                db.session.commit()
                session.pop("carrito", None)
                flash("¡Orden enviada con éxito! Te esperamos en sucursal.", "success")
                return redirect(url_for("ventas.online"))

            except exc.IntegrityError as e:
                db.session.rollback()
                # Este captura el error de la llave foránea (id_usuario 3 no existe)
                flash(f"Error de Integridad: El usuario registrado ({u_id}) no es válido en el sistema de ventas.", "danger")
                print(f"DEBUG FK ERROR: {str(e)}") # Esto lo verás en tu consola
                
            except exc.InternalError as e:
                db.session.rollback()
                # Este captura los SIGNAL de MySQL (Fecha, Stock, etc.)
                error_msg = str(e.orig).split("'")[1] if "'" in str(e.orig) else "Error en la validación del pedido"
                flash(f"Validación: {error_msg}", "warning")
                
            except Exception as e:
                db.session.rollback()
                # Error genérico para cualquier otra cosa
                flash(f"Error inesperado: {str(e)}", "danger")
            
            return redirect(url_for("ventas.online"))

    return render_template("ventas/online.html", form=form, lista_productos=productos)

# 💰 FORM PAGAR (OPERADOR / GERENTE)
@ventasBp.route("/<int:idVenta>/pagar", methods=["GET"], endpoint="form_pagar")
def form_pagar(idVenta):
    form = PagoForm()
    # Obtenemos el total de la base de datos para mostrarlo en el cuadro gris
    venta = db.session.execute(text("SELECT total FROM Ventas WHERE id_venta = :id"), {"id": idVenta}).fetchone()
    return render_template("ventas/pagar.html", form=form, idVenta=idVenta, total=venta.total if venta else 0)



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