from datetime import datetime
from flask import render_template, current_app
from flask_login import login_required, current_user
from app.blueprints.home import home_bp
from app.models import Statistic, Sector, Project, Partner, Article, PillarIcon, UserNotification


@home_bp.route("/health")
def health_check():
    return "OK"


@home_bp.route("/test")
def test_route():
    import sys
    import os
    from flask import current_app
    info = [
        "CHERE Test Route",
        f"Python: {sys.version}",
        f"FLASK_CONFIG: {os.getenv('FLASK_CONFIG', 'not set')}",
        f"DATABASE_URL env var: {'set' if os.getenv('DATABASE_URL') else 'not set'}",
        f"SQLALCHEMY_DATABASE_URI: {current_app.config.get('SQLALCHEMY_DATABASE_URI', 'not set')}",
    ]
    return "<br>".join(info)


@home_bp.route("/notifications")
@login_required
def notifications():
    unread_items = current_user.notifications.filter_by(is_read=False).all()
    for item in unread_items:
        item.is_read = True
        item.read_at = datetime.utcnow()
    from app.extensions import db
    db.session.commit()
    user_notifications = current_user.notifications.order_by(UserNotification.created_at.desc()).all()
    return render_template("notifications.html", notifications=user_notifications)


@home_bp.route("/")
def index():
    try:
        stats = Statistic.query.order_by(Statistic.order).all()
        sectors = Sector.query.filter_by(is_published=True).order_by(Sector.order).limit(12).all()
        projects = Project.query.filter_by(is_published=True).order_by(Project.created_at.desc()).limit(6).all()
        coming_soon = Project.query.filter_by(status="coming_soon", is_published=True).limit(3).all()
        partners = Partner.query.filter_by(is_published=True).order_by(Partner.order).all()
        articles = Article.query.filter_by(is_published=True).order_by(Article.published_at.desc()).limit(3).all()
        innovation_icons = PillarIcon.query.filter_by(pillar="innovation").order_by(PillarIcon.order).limit(8).all()
        renewable_icons = PillarIcon.query.filter_by(pillar="renewable").order_by(PillarIcon.order).limit(8).all()
        humanitarian_icons = PillarIcon.query.filter_by(pillar="humanitarian").order_by(PillarIcon.order).limit(8).all()

        return render_template(
            "home/index.html",
            stats=stats,
            sectors=sectors,
            projects=projects,
            coming_soon=coming_soon,
            partners=partners,
            articles=articles,
            innovation_icons=innovation_icons,
            renewable_icons=renewable_icons,
            humanitarian_icons=humanitarian_icons,
        )
    except Exception as e:
        current_app.logger.exception("Error loading index route")
        raise
