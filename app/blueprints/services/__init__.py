from flask import Blueprint

services_bp = Blueprint("services", __name__, template_folder="../../templates/services")

from app.blueprints.services import routes  # noqa: E402,F401
