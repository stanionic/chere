from flask import render_template
from app.blueprints.renewable import renewable_bp
from app.models import PillarIcon, Service


@renewable_bp.route("/")
def index():
    icons = PillarIcon.query.filter_by(pillar="renewable").order_by(PillarIcon.order).all()
    services = Service.query.filter_by(pillar="renewable", is_published=True).all()
    return render_template("renewable/index.html", icons=icons, services=services, pillar="renewable")
