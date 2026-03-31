# Rutas para la gestión de proveedores
from . import proveedores
from flask import render_template, request, redirect, url_for, flash
from model import db, Proveedores
from sqlalchemy.exc import IntegrityError
from forms import ProveedorForm


@proveedores.route('/proveedores')
def index():
    """Lista todos los proveedores"""
    busqueda = request.args.get('busqueda', '')
    estado   = request.args.get('estado', 'todos')

    query = Proveedores.query

    if busqueda:
        query = query.filter(
            db.or_(
                Proveedores.nombre.ilike(f'%{busqueda}%'),
                Proveedores.rfc.ilike(f'%{busqueda}%')
            )
        )

    if estado == 'activos':
        query = query.filter(Proveedores.estado == True)
    elif estado == 'inactivos':
        query = query.filter(Proveedores.estado == False)

    proveedores_list = query.order_by(Proveedores.nombre).all()

    return render_template('proveedores/listadoProvee.html',
                           proveedores=proveedores_list,
                           busqueda=busqueda,
                           estado=estado)


@proveedores.route('/proveedores/nuevo', methods=['GET', 'POST'])
def nuevo():
    """Registrar nuevo proveedor"""
    form = ProveedorForm()

    if form.validate_on_submit():
        existente = Proveedores.query.filter_by(rfc=form.rfc.data.upper()).first()
        if existente:
            flash(f'Ya existe un proveedor con el RFC {form.rfc.data}', 'error')
        else:
            try:
                proveedor = Proveedores(
                    nombre=form.nombre.data,
                    rfc=form.rfc.data.upper(),
                    telefono=form.telefono.data or None,
                    email=form.email.data or None,
                    direccion=form.direccion.data or None
                )
                db.session.add(proveedor)
                db.session.commit()
                flash(f'Proveedor {proveedor.nombre} registrado exitosamente', 'success')
                return redirect(url_for('proveedores.index'))
            except IntegrityError:
                db.session.rollback()
                flash('Error: No se pudo registrar el proveedor. Verifica los datos.', 'error')

    return render_template('proveedores/registrarProve.html', form=form)


@proveedores.route('/proveedores/detalle/<int:id>')
def detalle(id):
    """Ver detalle de un proveedor"""
    proveedor = db.get_or_404(Proveedores, id)
    return render_template('proveedores/detalleProve.html', proveedor=proveedor)


@proveedores.route('/proveedores/modificar/<int:id>', methods=['GET', 'POST'])
def modificar(id):
    """Modificar proveedor existente"""
    proveedor = db.get_or_404(Proveedores, id)
    # obj=proveedor pre-puebla el formulario en GET; en POST usa request.form
    form = ProveedorForm(obj=proveedor)

    if form.validate_on_submit():
        existente = Proveedores.query.filter(
            Proveedores.rfc == form.rfc.data.upper(),
            Proveedores.id != id
        ).first()

        if existente:
            flash(f'Ya existe otro proveedor con el RFC {form.rfc.data}', 'error')
        else:
            try:
                proveedor.nombre    = form.nombre.data
                proveedor.rfc       = form.rfc.data.upper()
                proveedor.telefono  = form.telefono.data or None
                proveedor.email     = form.email.data or None
                proveedor.direccion = form.direccion.data or None
                db.session.commit()
                flash(f'Proveedor {proveedor.nombre} actualizado exitosamente', 'success')
                return redirect(url_for('proveedores.index'))
            except IntegrityError:
                db.session.rollback()
                flash('Error: No se pudo actualizar el proveedor.', 'error')

    return render_template('proveedores/modificarProve.html', form=form, proveedor=proveedor)


@proveedores.route('/proveedores/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar(id):
    """Desactivar proveedor (soft-delete)"""
    proveedor = db.get_or_404(Proveedores, id)

    if request.method == 'POST':
        try:
            proveedor.estado = False
            db.session.commit()
            flash(f'Proveedor {proveedor.nombre} desactivado exitosamente.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al desactivar el proveedor: {str(e)}', 'error')

        return redirect(url_for('proveedores.index'))

    return render_template('proveedores/eliminarProve.html', proveedor=proveedor)


@proveedores.route('/proveedores/reactivar/<int:id>')
def reactivar(id):
    """Reactivar proveedor desactivado"""
    proveedor = db.get_or_404(Proveedores, id)
    proveedor.estado = True

    try:
        db.session.commit()
        flash(f'Proveedor {proveedor.nombre} reactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al reactivar proveedor: {str(e)}', 'error')

    return redirect(url_for('proveedores.index'))
