import config
from flask import Flask, render_template
from database import db
from flask_wtf.csrf import CSRFProtect
from datetime import datetime

app = Flask(__name__)

# Configuración
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'urban-coffee-secret-key-2024'

# Inicializar extensiones
db.init_app(app)
csrf = CSRFProtect(app)

# Registrar blueprints
from app.utilidad import utilidad
app.register_blueprint(utilidad)

# Context processor para variables globales en todos los templates
@app.context_processor
def inject_globals():
    return {'now': datetime.now()}

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
