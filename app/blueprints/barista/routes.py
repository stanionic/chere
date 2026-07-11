from flask import render_template
from app.blueprints.barista import barista_bp


@barista_bp.route("/")
def index():
    return render_template("barista/index.html")


@barista_bp.route("/card")
def card():
    return render_template("barista/card.html")
