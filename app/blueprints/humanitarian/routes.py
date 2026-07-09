from flask import render_template
from app.blueprints.humanitarian import humanitarian_bp
from app.models import PillarIcon, Service


@humanitarian_bp.route("/")
def index():
    icons = PillarIcon.query.filter_by(pillar="humanitarian").order_by(PillarIcon.order).all()
    services = Service.query.filter_by(pillar="humanitarian", is_published=True).all()
    return render_template("humanitarian/index.html", icons=icons, services=services, pillar="humanitarian")
