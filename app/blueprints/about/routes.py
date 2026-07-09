from flask import render_template
from app.blueprints.about import about_bp
from app.models import TeamMember, Statistic


@about_bp.route("/")
def index():
    team = TeamMember.query.filter_by(is_published=True).order_by(TeamMember.order).all()
    stats = Statistic.query.order_by(Statistic.order).all()
    return render_template("about/index.html", team=team, stats=stats)
