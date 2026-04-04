from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Inicializamos la base de datos (se configurará con la app abajo)
from model import db

def create_app():
    app = Flask(__name__)

    # Configuración básica (Asegúrate de tener un config.py en la raíz)
    app.config['SECRET_KEY'] = 'clave_secreta_urban_coffe'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urbancoffe.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Unir la base de datos a la aplicación
    db.init_app(app)

    # --- REGISTRO DE BLUEPRINTS (Tus módulos) ---
    
    # 1. Registro del módulo de Usuarios (el que ya tienes)
    from .usuarios.routes import usuariosBp
    app.register_blueprint(usuariosBp)

    # 2. Aquí registrarás tu módulo de Ventas cuando lo crees
    # from .ventas.routes import ventasBp
    # app.register_blueprint(ventasBp)

    # Crear las tablas en la base de datos si no existen (Solo para local)
    with app.app_context():
        db.create_all()

    return app