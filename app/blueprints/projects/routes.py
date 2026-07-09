from flask import render_template, request
from app.blueprints.projects import projects_bp
from app.models import Project


@projects_bp.route("/")
def index():
    status_filter = request.args.get("status")
    query = Project.query.filter_by(is_published=True)
    if status_filter:
        query = query.filter_by(status=status_filter)
    projects = query.order_by(Project.created_at.desc()).all()
    coming_soon = Project.query.filter_by(status="coming_soon", is_published=True).all()
    return render_template("projects/index.html", projects=projects, coming_soon=coming_soon)


@projects_bp.route("/<slug>")
def detail(slug):
    project = Project.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("projects/detail.html", project=project)
