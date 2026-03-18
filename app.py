
import os

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "urban-coffee-dev-secret-key")

APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin123")


@app.before_request
def require_login():
    allowed_endpoints = {"login", "static"}

    if request.endpoint in allowed_endpoints:
        return None

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return None

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if username == APP_USERNAME and password == APP_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))

        flash('Usuario o contraseña inválidos.', 'danger')

    return render_template('login/index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard/index.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)