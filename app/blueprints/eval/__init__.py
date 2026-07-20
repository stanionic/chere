from flask import Blueprint

eval_bp = Blueprint("eval", __name__, template_folder="../../templates/eval")

from app.blueprints.eval import routes  # noqa: E402,F401