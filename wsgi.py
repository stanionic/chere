import os
import logging
from app import create_app, db
from app.models import User, Role, Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app(os.getenv("FLASK_CONFIG", "production").strip())


def _bootstrap_db():
    with app.app_context():
        try:
            uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
            logger.info("DB URI: %s", uri[:40] if uri else "NOT SET")
            if not uri:
                raise RuntimeError("SQLALCHEMY_DATABASE_URI is not set")
            db.create_all()
            for name in ("admin", "editor", "viewer"):
                if not Role.query.filter_by(name=name).first():
                    db.session.add(Role(name=name))
            db.session.commit()
            admin_role = Role.query.filter_by(name="admin").first()
            if not User.query.filter_by(email="admin@chere-global.org").first():
                u = User(full_name="Admin CHERE", email="admin@chere-global.org", role_id=admin_role.id)
                u.set_password("ChangeMe123!")
                db.session.add(u)
                db.session.commit()
                logger.info("Admin user created.")
            _seed_events()
        except Exception:
            logger.exception("DB bootstrap failed")


def _seed_events():
    from datetime import datetime
    if Event.query.filter_by(slug="cooking-class").first():
        return
    event = Event(
        title="COOKING CLASS",
        slug="cooking-class",
        description="Join our hands-on cooking class and discover the art of preparing delicious meals. Learn techniques from professional chefs in a fun and interactive environment.",
        summary="Hands-on cooking class with professional chefs.",
        event_type="workshop",
        is_paid=True,
        price=1000.0,
        currency="RWF",
        location="CHERE Hub, Kigali",
        event_date=datetime(2026, 8, 15, 10, 0),
        is_published=True,
    )
    db.session.add(event)
    db.session.commit()
    logger.info("COOKING CLASS event seeded.")


_bootstrap_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
