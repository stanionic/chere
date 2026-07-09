from flask import render_template
from app.blueprints.partners import partners_bp
from app.models import Partner


@partners_bp.route("/")
def index():
    partners = Partner.query.filter_by(is_published=True).order_by(Partner.order).all()
    return render_template("partners/index.html", partners=partners)
