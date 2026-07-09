from flask import Blueprint

blog_bp = Blueprint("blog", __name__, template_folder="../../templates/blog")

from app.blueprints.blog import routes  # noqa: E402,F401
