"""
Application factory CHERE.
"""
from flask import Flask, render_template
from app.config import config
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name="development"):
    app = Flask(__name__)
    config_name = (config_name or "development").strip()
    if config_name not in config:
        config_name = "development"
    app.config.from_object(config[config_name]())

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.blueprints.home import home_bp
    from app.blueprints.about import about_bp
    from app.blueprints.services import services_bp
    from app.blueprints.innovation import innovation_bp
    from app.blueprints.renewable import renewable_bp
    from app.blueprints.humanitarian import humanitarian_bp
    from app.blueprints.projects import projects_bp
    from app.blueprints.partners import partners_bp
    from app.blueprints.blog import blog_bp
    from app.blueprints.contact import contact_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(about_bp, url_prefix="/about")
    app.register_blueprint(services_bp, url_prefix="/services")
    app.register_blueprint(innovation_bp, url_prefix="/innovation")
    app.register_blueprint(renewable_bp, url_prefix="/renewable-energy")
    app.register_blueprint(humanitarian_bp, url_prefix="/humanitarian")
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(partners_bp, url_prefix="/partners")
    app.register_blueprint(blog_bp, url_prefix="/blog")
    app.register_blueprint(contact_bp, url_prefix="/contact")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {
            "site_name": app.config["SITE_NAME"],
            "site_tagline": app.config["SITE_TAGLINE"],
            "current_year": datetime.utcnow().year,
        }

    return app


from app.models import User  # noqa: E402


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
