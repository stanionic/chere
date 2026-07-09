from flask import Blueprint

about_bp = Blueprint("about", __name__, template_folder="../../templates/about")

from app.blueprints.about import routes  # noqa: E402,F401
