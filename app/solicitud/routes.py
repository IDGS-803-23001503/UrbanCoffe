from flask import Blueprint, render_template, request, redirect, url_for, session
from model import db, SolicitudProduccion, DetalleProduccion, Producto

solicitud_bp = Blueprint('solicitud', __name__)

@solicitud_bp.route('/')
def index():
    solicitudes = SolicitudProduccion.query.order_by(SolicitudProduccion.fecha.desc()).all()
    return render_template('solicitud/index.html', solicitudes=solicitudes)

@solicitud_bp.route('/crear')
def crear_solicitud():
    # se esta usando este id_usuario temporalmente hasta que se integre con login
    id_usuario = 1
    
    #cuando ya se integre todo se tendra que usar esto de aqui para obtener el id del usuario logueado
    #id_usuario = session.get('usuarioId')
    
    nueva_solicitud = SolicitudProduccion(id_usuario=id_usuario)
    db.session.add(nueva_solicitud)
    db.session.commit()
    
    return redirect(url_for('solicitud.detalles_solicitud', id=nueva_solicitud.id_solicitud))

@solicitud_bp.route('/<int:id>/detalles', methods=['GET', 'POST'])
def detalles_solicitud(id):
    solicitud = SolicitudProduccion.query.get_or_404(id)
    productos_disponibles = Producto.query.filter_by(estatus=True).all()

    if request.method == 'POST':
        id_producto = request.form.get('id_producto')
        cantidad = request.form.get('cantidad')
        nuevo_detalle = DetalleProduccion(
            id_solicitud=solicitud.id_solicitud,
            id_producto=id_producto,
            cantidad=cantidad
        )
        db.session.add(nuevo_detalle)
        db.session.commit()
        
        return redirect(url_for('solicitud.detalles_solicitud', id=solicitud.id_solicitud))

    return render_template('solicitud/detalles.html', solicitud=solicitud, productos=productos_disponibles)