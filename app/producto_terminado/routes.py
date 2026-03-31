from flask import Blueprint, render_template, request
from model import db, Producto

producto_bp = Blueprint('producto_terminado', __name__)

@producto_bp.route('/catalogo')
def index():
    busqueda = request.args.get('q')
    
    if busqueda:
        productos = Producto.query.filter(Producto.nombre.like(f'%{busqueda}%')).all()
    else:
        productos = Producto.query.all()
        
    return render_template('producto_terminado/index.html', productos=productos, busqueda=busqueda)

@producto_bp.route('/nuevo-producto', methods=['GET', 'POST'])
def nuevo_producto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        categoria = request.form.get('categoria')
        precio_venta = request.form.get('precio_venta')

        nuevo_producto = Producto(
            nombre=nombre,
            categoria=categoria,
            precio_venta=precio_venta
        )

        db.session.add(nuevo_producto)
        db.session.commit()
        
        return render_template('producto_terminado/nuevo_producto.html', mostrar_modal=True)
    
    return render_template('producto_terminado/nuevo_producto.html', mostrar_modal=False)

@producto_bp.route('/editar-producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        producto.nombre = request.form.get('nombre')
        producto.categoria = request.form.get('categoria')
        producto.precio_venta = request.form.get('precio_venta')
        estatus_form = request.form.get('estatus')
        producto.estatus = True if estatus_form == '1' else False
        db.session.commit()
        
        return render_template('producto_terminado/editar_producto.html', mostrar_modal=True, producto=producto)
    
    return render_template('producto_terminado/editar_producto.html', mostrar_modal=False, producto=producto)