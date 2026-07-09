from flask import render_template
from app.blueprints.home import home_bp
from app.models import Statistic, Sector, Project, Partner, Article, PillarIcon


@home_bp.route("/health")
def health_check():
    return "OK"


@home_bp.route("/")
def index():
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
