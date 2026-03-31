from flask import Blueprint

proveedores = Blueprint('proveedores', __name__)

from . import routes
