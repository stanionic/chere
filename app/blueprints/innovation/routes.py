from flask import render_template
from app.blueprints.innovation import innovation_bp
from app.models import PillarIcon, Service


@innovation_bp.route("/")
def index():
    icons = PillarIcon.query.filter_by(pillar="innovation").order_by(PillarIcon.order).all()
    services = Service.query.filter_by(pillar="innovation", is_published=True).all()
    return render_template("innovation/index.html", icons=icons, services=services, pillar="innovation")
