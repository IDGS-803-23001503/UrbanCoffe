from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from model import User, db

auth_bp = Blueprint("auth", __name__)

DUMMY_PASSWORD_HASH = generate_password_hash("urban-coffee-dummy-password")


def seed_default_users() -> None:
	gerente = User.query.filter_by(correo="gerente@urbancoffee.com").first()
	operador = User.query.filter_by(correo="operador@urbancoffee.com").first()

	if not gerente:
		gerente = User(correo="gerente@urbancoffee.com", rol="Gerente")
		gerente.set_password("Gerente#2026")
		db.session.add(gerente)

	if not operador:
		operador = User(correo="operador@urbancoffee.com", rol="Operador")
		operador.set_password("Operador#2026")
		db.session.add(operador)

	db.session.commit()


def init_auth_module(app) -> None:
	with app.app_context():
		db.create_all()
		seed_default_users()


def user_is_authenticated() -> bool:
	return bool(session.get("logged_in") and session.get("user_id"))


def role_dashboard_endpoint(role: str) -> str:
	role_map = {
		"Gerente": "dashboard_gerente",
		"Operador": "dashboard_operador",
	}
	return role_map.get(role, "dashboard_operador")


@auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
	if request.method == "POST":
		email = request.form.get("email", "").strip().lower()
		password = request.form.get("password", "")

		generic_error = "Usuario o contraseña incorrectos"
		user = User.query.filter_by(correo=email).first()

		if not user:
			check_password_hash(DUMMY_PASSWORD_HASH, password)
			flash(generic_error, "danger")
			return render_template("login.html")

		if user.esta_bloqueada():
			db.session.commit()
			flash("Cuenta bloqueada temporalmente.", "warning")
			return render_template("login.html")

		if not user.check_password(password):
			user.registrar_intento_fallido(max_intentos=3, minutos_bloqueo=15)
			db.session.commit()

			if user.cuenta_bloqueada:
				flash("Cuenta bloqueada temporalmente.", "warning")
			else:
				flash(generic_error, "danger")

			return render_template("login.html")

		user.resetear_seguridad()
		db.session.commit()

		session.clear()
		session.permanent = True
		session["logged_in"] = True
		session["user_id"] = user.id
		session["user_email"] = user.correo
		session["user_role"] = user.rol

		return redirect(url_for(role_dashboard_endpoint(user.rol)))

	return render_template("login.html")


@auth_bp.route("/forgot-password", endpoint="forgot_password")
def forgot_password():
	flash("Espera espera espera test.", "info")
	return redirect(url_for("auth.login"))


@auth_bp.route("/logout", endpoint="logout")
def logout():
	session.clear()
	return redirect(url_for("auth.login"))