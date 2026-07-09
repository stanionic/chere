from flask import Blueprint

renewable_bp = Blueprint("renewable", __name__, template_folder="../../templates/renewable")

from app.blueprints.renewable import routes  # noqa: E402,F401
