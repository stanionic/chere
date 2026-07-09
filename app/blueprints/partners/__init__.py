from flask import Blueprint

partners_bp = Blueprint("partners", __name__, template_folder="../../templates/partners")

from app.blueprints.partners import routes  # noqa: E402,F401
