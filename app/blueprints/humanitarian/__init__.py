from flask import Blueprint

humanitarian_bp = Blueprint("humanitarian", __name__, template_folder="../../templates/humanitarian")

from app.blueprints.humanitarian import routes  # noqa: E402,F401
