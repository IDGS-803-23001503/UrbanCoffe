from datetime import timedelta

from flask import Flask, abort, redirect, render_template, request, session, url_for
from sqlalchemy.exc import OperationalError

from config import Config
from app.login.routes import auth_bp, init_auth_module, role_dashboard_endpoint, user_is_authenticated
from model import db

app = Flask(__name__)
app.config.from_object(Config)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

db.init_app(app)
app.register_blueprint(auth_bp)
try:
    init_auth_module(app)
except OperationalError as exc:
    raise RuntimeError(
        "No fue posible conectar a MySQL."
    ) from exc


@app.before_request
def require_login():
    public_endpoints = {"auth.login", "auth.forgot_password", "index", "static"}

    if request.endpoint in public_endpoints:
        return None

    if not user_is_authenticated():
        return redirect(url_for("auth.login"))

    return None


@app.route("/")
def index():
    if user_is_authenticated():
        endpoint = role_dashboard_endpoint(session.get("user_role", "Operador"))
        return redirect(url_for(endpoint))
    return redirect(url_for("auth.login"))


@app.route("/dashboard/gerente")
def dashboard_gerente():
    if session.get("user_role") != "Gerente":
        abort(403)
    return render_template("dashboard/index.html")


@app.route("/dashboard/operador")
def dashboard_operador():
    if session.get("user_role") not in {"Gerente", "Operador"}:
        abort(403)
    return render_template("dashboard/index.html")


if __name__ == "__main__":
    app.run(debug=True)