from flask import Blueprint

pos_bp = Blueprint('pos', __name__, static_folder='static', template_folder='templates')

from app.blueprints.pos import routes
