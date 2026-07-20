import os
from flask import render_template, send_from_directory, current_app, Blueprint
from app.blueprints.eval import eval_bp


@eval_bp.route("/")
def index():
    """Serve the Plateforme Eval React app."""
    return render_template("eval/index.html")


@eval_bp.route("/assets/<path:filename>")
def assets(filename):
    """Serve static assets from the built plateforme-eval app."""
    assets_dir = os.path.join(current_app.root_path, "..", "plateforme-eval", "dist", "assets")
    return send_from_directory(assets_dir, filename)