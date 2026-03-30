from flask import Flask, render_template
from config import Config
from model import db
from app.inventario.routes import inventario_bp
from app.producto_terminado.routes import producto_bp
from app.solicitud.routes import solicitud_bp

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(inventario_bp, url_prefix='/inventario')

app.register_blueprint(producto_bp, url_prefix='/productos')

app.register_blueprint(solicitud_bp, url_prefix='/solicitudes')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)