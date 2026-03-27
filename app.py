from flask import Flask, render_template
from config import Config
from model import db
from app.inventario.routes import inventario_bp

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(inventario_bp, url_prefix='/inventario')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)