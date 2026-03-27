import os
from urllib.parse import quote_plus

class Config:
    # Agregamos una clave secreta por defecto que Flask suele pedir
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "urban-coffee-dev-secret-key")

    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Enchiladaverde5$')
    
    # Asegúrate de que el nombre coincida con el de tu script SQL
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'Urban_Coffee')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )