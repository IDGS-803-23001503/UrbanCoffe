from flask import Blueprint


utilidad = Blueprint(
    'utilidad',
    __name__,
    template_folder='templates',
    static_folder='static'
)
from . import routes
