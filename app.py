from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
import config


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Clave secreta necesaria para CSRF y sesiones
    app.config['SECRET_KEY'] = 'urban-coffee-dev-secret-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    from model import db
    db.init_app(app)

    csrf = CSRFProtect()
    csrf.init_app(app)

    # Registrar blueprints
    from app.proveedores import proveedores as proveedores_bp
    app.register_blueprint(proveedores_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app


app = create_app()

if __name__ == '__main__':
    from model import db
    with app.app_context():
        # Crea tablas que no existan aún (no modifica las existentes)
        db.create_all()
    app.run(debug=True)
