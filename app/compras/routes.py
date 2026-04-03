from . import compras
from flask import render_template, request, redirect, url_for, flash, jsonify
from model import db, Compra, DetalleCompra, Proveedor, MateriaPrima, UnidadMedida
from sqlalchemy import func
from datetime import datetime
import forms
from decimal import Decimal


@compras.route('/compras')
def index():
    return redirect(url_for('compras.listar'))


@compras.route('/compras/listar')
def listar():
    """Lista todas las compras con filtros"""
    filtro_form = forms.FiltroComprasForm(request.args)

    query = Compra.query

    if filtro_form.fecha_inicio.data:
        query = query.filter(func.date(Compra.fecha) >= filtro_form.fecha_inicio.data)
    if filtro_form.fecha_fin.data:
        query = query.filter(func.date(Compra.fecha) <= filtro_form.fecha_fin.data)
    if filtro_form.id_proveedor.data and filtro_form.id_proveedor.data != 0:
        query = query.filter(Compra.id_proveedor == filtro_form.id_proveedor.data)

    compras_list = query.order_by(Compra.fecha.desc()).all()

    return render_template('compras/index.html',
                           compras=compras_list,
                           filtro_form=filtro_form)


@compras.route('/compras/nueva', methods=['GET', 'POST'])
def nueva():
    """Registrar nueva compra"""
    form = forms.CompraForm(request.form)

    if request.method == 'POST' and form.validate():
        try:
            compra = Compra(
                id_proveedor=form.id_proveedor.data,
                fecha=form.fecha.data,
                precio_total=0
            )
            db.session.add(compra)
            db.session.flush()

            materias_ids = request.form.getlist('materia_id[]')
            cantidades   = request.form.getlist('cantidad[]')
            costos       = request.form.getlist('costo_unitario[]')
            unidades_ids = request.form.getlist('unidad_id[]')

            if not any(m for m in materias_ids if m):
                flash('Debe agregar al menos un insumo a la compra', 'error')
                db.session.rollback()
                return redirect(url_for('compras.nueva'))

            total_compra = Decimal('0')

            for i in range(len(materias_ids)):
                if materias_ids[i] and cantidades[i] and costos[i]:
                    materia_id     = int(materias_ids[i])
                    cantidad       = Decimal(cantidades[i])
                    costo_unitario = Decimal(costos[i])
                    unidad_id      = int(unidades_ids[i]) if unidades_ids[i] else None
                    subtotal       = cantidad * costo_unitario
                    total_compra  += subtotal

                    detalle = DetalleCompra(
                        id_compra=compra.id_compra,
                        id_materia=materia_id,
                        cantidad=float(cantidad),
                        unidad=unidad_id,
                        costo_unitario=float(costo_unitario),
                        subtotal=float(subtotal)
                    )
                    db.session.add(detalle)

                    materia = MateriaPrima.query.get(materia_id)
                    if materia:
                        materia.actualizar_stock(cantidad, costo_unitario)

            compra.precio_total = float(total_compra)
            db.session.commit()
            flash(f'Compra registrada exitosamente. Total: ${float(total_compra):.2f}', 'success')
            return redirect(url_for('compras.detalle', id=compra.id_compra))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar la compra: {str(e)}', 'error')
            return redirect(url_for('compras.nueva'))

    proveedores     = Proveedor.query.filter_by(estatus=True).all()
    materias_primas = MateriaPrima.query.all()
    unidades        = UnidadMedida.query.all()

    return render_template('compras/registrarCompra.html',
                           form=form,
                           proveedores=proveedores,
                           materias_primas=materias_primas,
                           unidades=unidades,
                           datetime=datetime)


@compras.route('/compras/detalle/<int:id>')
def detalle(id):
    """Ver detalle de una compra específica"""
    compra = Compra.query.get_or_404(id)
    return render_template('compras/detalleCompra.html', compra=compra)


@compras.route('/compras/obtener_materia/<int:materia_id>')
def obtener_materia(materia_id):
    """API para obtener datos de una materia prima"""
    materia = MateriaPrima.query.get_or_404(materia_id)
    return jsonify({
        'id':            materia.id_materia,
        'nombre':        materia.nombre,
        'unidad_id':     materia.unidad_medida,
        'unidad_nombre': materia.unidad.abreviacion if materia.unidad else 'ud',
        'stock_actual':  float(materia.stock_actual) if materia.stock_actual else 0
    })