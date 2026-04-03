from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from model import db, Merma, MateriaPrima
from forms import MermaForm

merma_bp = Blueprint('merma', __name__, url_prefix='/mermas')

@merma_bp.route('/merma', methods=['GET'])
def merma():
    
    fecha_inicio = request.args.get('inicio')
    fecha_fin = request.args.get('fin')

    query = Merma.query
    
    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            query = query.filter(Merma.fecha >= fecha_inicio)

        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            query = query.filter(Merma.fecha <= fecha_fin)

    except ValueError:
        flash('Formato de fecha inválido', 'danger')
        return redirect(url_for('merma.merma'))

    mermas = query.order_by(Merma.fecha.desc()).all()

    return render_template('merma/merma.html', mermas=mermas)


@merma_bp.route('/nueva_merma', methods=['GET', 'POST'])
def nueva_merma():
    
    form = MermaForm()
    
    form.materia_id.choices = [
        (m.id_materia, m.nombre) for m in MateriaPrima.query.all()
    ]

    if form.validate_on_submit():

        try:

            materia = MateriaPrima.query.get(form.materia_id.data)

            if not materia:
                raise ValueError("Materia prima no encontrada")

            if form.cantidad.data > materia.stock_actual:
                raise ValueError("No hay suficiente stock disponible")
            
            materia.stock_actual -= form.cantidad.data

            merma = Merma(
                cantidad=form.cantidad.data,
                fecha=form.fecha.data,
                motivo=form.motivo.data,
                materia_id=materia.id_materia,
                usuario_id=session.get("usuarioId")
            )

            db.session.add(merma)
            db.session.commit()

            flash('Merma registrada correctamente', 'success')
            return redirect(url_for('merma.merma'))

        except Exception as e:
            db.session.rollback()
            flash(str(e), 'danger')

    return render_template('merma/nueva_merma.html', form=form)