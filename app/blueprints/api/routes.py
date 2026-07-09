"""
API JSON légère utilisée par le frontend (compteurs animés, carte des projets, ...).
"""
from flask import jsonify
from app.blueprints.api import api_bp
from app.models import Statistic, Project


@api_bp.route("/stats")
def stats():
    data = [
        {"label": s.label, "value": s.value, "suffix": s.suffix, "icon": s.icon}
        for s in Statistic.query.order_by(Statistic.order).all()
    ]
    return jsonify(data)


@api_bp.route("/projects/map")
def projects_map():
    projects = Project.query.filter_by(is_published=True).filter(
        Project.latitude.isnot(None), Project.longitude.isnot(None)
    ).all()
    data = [
        {
            "title": p.title,
            "country": p.country,
            "continent": p.continent,
            "lat": p.latitude,
            "lng": p.longitude,
            "status": p.status,
            "pillar": p.pillar,
            "slug": p.slug,
        }
        for p in projects
    ]
    return jsonify(data)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "CHERE API"})
