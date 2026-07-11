from flask import Blueprint

barista_bp = Blueprint("barista", __name__, template_folder="../../templates/barista")

from app.blueprints.barista import routes  # noqa: E402,F401
