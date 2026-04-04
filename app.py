from datetime import timedelta
from flask import Flask, abort, redirect, render_template, request, session, url_for
from sqlalchemy.exc import OperationalError
from config import Config
from model import db

# Importación de los módulos de tus compañeros
from app.login.routes import authBp, endpointDashboardRol, iniciarModuloAuth, usuarioAutenticado
from app.usuarios.routes import usuariosBp
from app.ventas.routes import ventasBp
from app.pedidos.routes import pedidosBp
from app.clientes.routes import clientesBp
from app.inventario.routes import inventario_bp

app = Flask(__name__)
app.config.from_object(Config)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

db.init_app(app)

# Registro de todos los Blueprints
app.register_blueprint(authBp)
app.register_blueprint(ventasBp)
app.register_blueprint(pedidosBp)
app.register_blueprint(usuariosBp)
app.register_blueprint(clientesBp)
app.register_blueprint(inventario_bp, url_prefix='/inventario')

# Intentar conectar a la base de datos
with app.app_context():
    try:
        db.create_all()  # Crea las tablas si no existen
        iniciarModuloAuth(app)
    except Exception as exc:
        print(f"Error al inicializar: {exc}")

@app.before_request
def requerirLogin():
    # Endpoints que no necesitan estar logueado
    endpointsPublicos = {"auth.iniciarSesion", "auth.registrarUsuario", "auth.recuperarContrasena", "index", "static"}
    
    if request.endpoint in endpointsPublicos or not request.endpoint:
        return None

    if not usuarioAutenticado():
        return redirect(url_for("auth.iniciarSesion"))
    return None

@app.route("/")
def index():
    if usuarioAutenticado():
        endpointRol = endpointDashboardRol(session.get("usuarioRol", "Operador"))
        return redirect(url_for(endpointRol))
    return redirect(url_for("auth.iniciarSesion"))

@app.route("/dashboard/gerente")
def dashboard_gerente():
    if session.get("usuarioRol") != "Gerente":
        abort(403)
    return render_template("dashboard/index.html")

@app.route("/dashboard/operador")
def dashboard_operador():
    if session.get("usuarioRol") not in {"Gerente", "Operador"}:
        abort(403)
    return render_template("dashboard/index.html")

if __name__ == "__main__":
    app.run(debug=True)