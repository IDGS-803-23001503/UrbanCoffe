from flask import Blueprint, render_template, request

from model import db, MateriaPrima

inventario_bp = Blueprint('inventario', __name__)

@inventario_bp.route('/materias-primas')
def materias_primas():
    busqueda = request.args.get('q')
    
    if busqueda:
        insumos = MateriaPrima.query.filter(MateriaPrima.nombre.like(f'%{busqueda}%')).all()
    else:
        insumos = MateriaPrima.query.all()
    
    nombres_unidades = {
        1: 'Kilogramos (kg)', 
        2: 'Litros (L)', 
        3: 'Gramos (g)', 
        4: 'Piezas (pz)'
    }
    
    return render_template('inventario/index.html', insumos=insumos, unidades=nombres_unidades, busqueda=busqueda)

@inventario_bp.route('/nueva-materia', methods=['GET', 'POST'])
def nueva_materia():
    if request.method == 'POST':
        nombre = request.form.get('nombre_insumo')
        descripcion = request.form.get('descripcion')
        unidad_medida = request.form.get('unidad_medida') 
        stock_minimo = request.form.get('stock_minimo')

        nuevo_insumo = MateriaPrima(
            nombre=nombre,
            descripcion=descripcion,
            unidad_medida=unidad_medida, 
            stock_minimo=stock_minimo,
            stock_actual=0.0 
        )

        # Guardamos en la base de datos
        db.session.add(nuevo_insumo)
        db.session.commit()
        
        return render_template('inventario/nueva_materia.html', mostrar_modal=True)
    
    return render_template('inventario/nueva_materia.html', mostrar_modal=False)

@inventario_bp.route('/editar-materia/<int:id>', methods=['GET', 'POST'])
def editar_materia(id):
    insumo = MateriaPrima.query.get_or_404(id)

    if request.method == 'POST':
        insumo.nombre = request.form.get('nombre_insumo')
        insumo.descripcion = request.form.get('descripcion')
        insumo.unidad_medida = request.form.get('unidad_medida')
        insumo.stock_minimo = request.form.get('stock_minimo')

        db.session.commit()
        
        return render_template('inventario/editar_materia.html', mostrar_modal=True, insumo=insumo)
    
    return render_template('inventario/editar_materia.html', mostrar_modal=False, insumo=insumo)