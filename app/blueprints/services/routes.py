from flask import render_template
from app.blueprints.services import services_bp
from app.models import Sector


@services_bp.route("/")
def index():
    sectors = Sector.query.filter_by(is_published=True).order_by(Sector.order).all()
    return render_template("services/index.html", sectors=sectors)
