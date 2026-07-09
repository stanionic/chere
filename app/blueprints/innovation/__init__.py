from flask import Blueprint

innovation_bp = Blueprint("innovation", __name__, template_folder="../../templates/innovation")

from app.blueprints.innovation import routes  # noqa: E402,F401
