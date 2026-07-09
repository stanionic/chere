from flask import Blueprint

projects_bp = Blueprint("projects", __name__, template_folder="../../templates/projects")

from app.blueprints.projects import routes  # noqa: E402,F401
