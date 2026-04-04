from flask import Blueprint, render_template, session, redirect, url_for
from model import db
from sqlalchemy import text 

pedidosBp = Blueprint("pedidos", __name__, url_prefix="/pedidos")

# 📦 PEDIDOS DEL CLIENTE
@pedidosBp.route("/mis-pedidos", methods=["GET"], endpoint="mis_pedidos")
def mis_pedidos():
    # Cambiado de 'Pedido' a 'pedidos' y de 'Ventas' a 'ventas' (ajusta si ventas es con V mayúscula)
    query = text("""
        SELECT p.*, v.codigo_recogida
        FROM pedidos p
        JOIN ventas v ON p.id_venta = v.id_venta
        WHERE v.id_cliente = :cliente
        ORDER BY p.hora_solicitud DESC
    """)
    
    pedidos = db.session.execute(query, {"cliente": session.get("clienteId")}).fetchall()
    return render_template("pedidos/mis_pedidos.html", pedidos=pedidos)

# 📋 PANEL DEL OPERADOR (BARISTA)
@pedidosBp.route("/", methods=["GET"], endpoint="index")
def index():
    # La consulta SQL está perfecta, el cambio es cómo procesamos el resultado
    query = text("""
        SELECT 
            p.id_pedido, 
            p.id_venta, 
            p.hora_recogida, 
            p.estado, 
            p.notas, 
            v.codigo_recogida,
            c.nombre AS nombre_cliente
        FROM pedidos p
        JOIN ventas v ON p.id_venta = v.id_venta
        LEFT JOIN clientes c ON v.id_cliente = c.id_cliente
        WHERE p.estado IN ('pendiente', 'Preparando', 'Listo')
        ORDER BY p.hora_recogida ASC
    """)
    
    # 1. Ejecutamos la consulta
    result = db.session.execute(query)
    
    # 2. CONVERTIMOS A DICCIONARIO: Esto es lo que soluciona el problema.
    # Transformamos cada fila en un diccionario para que el HTML entienda p.id_pedido
    pedidos = [dict(row._mapping) for row in result]
    
    # Debug opcional: imprime en consola para ver si hay datos
    # print(f"DEBUG: Pedidos encontrados: {len(pedidos)}")
    
    return render_template("pedidos/pedidos.html", pedidos=pedidos)
# 🔄 CAMBIAR ESTADO
@pedidosBp.route("/<int:idPedido>/estado/<string:estado>", methods=["POST"])
def cambiar_estado(idPedido, estado):
    query = text("""
        UPDATE pedidos
        SET estado = :estado
        WHERE id_pedido = :id
    """)
    
    db.session.execute(query, {"estado": estado, "id": idPedido})
    db.session.commit()

    return redirect(url_for("pedidos.index"))