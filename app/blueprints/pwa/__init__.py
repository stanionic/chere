from flask import Blueprint

pwa_bp = Blueprint("pwa", __name__, template_folder="../../templates/pwa")

from app.blueprints.pwa import routes  # noqa: E402,F401
