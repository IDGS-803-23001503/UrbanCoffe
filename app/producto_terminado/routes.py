from decimal import Decimal, InvalidOperation
from types import SimpleNamespace

from flask import Blueprint, flash, redirect, render_template, request, url_for

from model import ProductoTerminado, db

producto_bp = Blueprint('producto_terminado', __name__)


def _presentar_producto(producto: ProductoTerminado) -> SimpleNamespace:
    return SimpleNamespace(
        id_producto=producto.id,
        nombre=producto.nombre,
        categoria="General",
        precio_venta=producto.precio,
        stock=producto.stockActual,
        estatus=producto.activo,
    )

@producto_bp.route('/catalogo')
def index():
    busqueda = request.args.get('q', '').strip()
    
    if busqueda:
        productos_db = ProductoTerminado.query.filter(ProductoTerminado.nombre.ilike(f'%{busqueda}%')).all()
    else:
        productos_db = ProductoTerminado.query.order_by(ProductoTerminado.nombre.asc()).all()

    productos = [_presentar_producto(p) for p in productos_db]
        
    return render_template('producto_terminado/index.html', productos=productos, busqueda=busqueda)

@producto_bp.route('/nuevo-producto', methods=['GET', 'POST'])
def nuevo_producto():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        precio_venta_raw = request.form.get('precio_venta', '').strip()

        if not nombre or not precio_venta_raw:
            flash('Completa nombre y precio.', 'danger')
            return render_template('producto_terminado/nuevo_producto.html', mostrar_modal=False)

        try:
            precio_venta = Decimal(precio_venta_raw)
        except (InvalidOperation, TypeError):
            flash('Precio inválido.', 'danger')
            return render_template('producto_terminado/nuevo_producto.html', mostrar_modal=False)

        if precio_venta <= 0:
            flash('El precio debe ser mayor a 0.', 'danger')
            return render_template('producto_terminado/nuevo_producto.html', mostrar_modal=False)

        nuevo_producto = ProductoTerminado(
            nombre=nombre,
            precio=precio_venta,
            stockActual=0,
            stockMinimo=0,
            activo=True,
        )

        db.session.add(nuevo_producto)
        db.session.commit()
        
        return render_template('producto_terminado/nuevo_producto.html', mostrar_modal=True)
    
    return render_template('producto_terminado/nuevo_producto.html', mostrar_modal=False)

@producto_bp.route('/editar-producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    producto_db = ProductoTerminado.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        precio_venta_raw = request.form.get('precio_venta', '').strip()
        estatus_form = request.form.get('estatus')

        if not nombre or not precio_venta_raw:
            flash('Completa nombre y precio.', 'danger')
            return render_template('producto_terminado/editar_producto.html', mostrar_modal=False, producto=_presentar_producto(producto_db))

        try:
            precio_venta = Decimal(precio_venta_raw)
        except (InvalidOperation, TypeError):
            flash('Precio inválido.', 'danger')
            return render_template('producto_terminado/editar_producto.html', mostrar_modal=False, producto=_presentar_producto(producto_db))

        if precio_venta <= 0:
            flash('El precio debe ser mayor a 0.', 'danger')
            return render_template('producto_terminado/editar_producto.html', mostrar_modal=False, producto=_presentar_producto(producto_db))

        producto_db.nombre = nombre
        producto_db.precio = precio_venta
        producto_db.activo = True if estatus_form == '1' else False
        db.session.commit()
        
        return render_template('producto_terminado/editar_producto.html', mostrar_modal=True, producto=_presentar_producto(producto_db))
    
    return render_template('producto_terminado/editar_producto.html', mostrar_modal=False, producto=_presentar_producto(producto_db))