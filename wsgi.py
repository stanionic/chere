import os
import logging
from app import create_app, db
from app.models import User, Role, Event, BaristaMenu

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
    if not Event.query.filter_by(slug="cooking-class").first():
        db.session.add(Event(
            title="COOKING CLASS",
            slug="cooking-class",
            description="Join our hands-on cooking class and discover the art of preparing delicious meals.",
            summary="Hands-on cooking class with professional chefs.",
            event_type="workshop",
            is_paid=True,
            price=1000.0,
            currency="RWF",
            location="CHERE Hub, Kigali",
            event_date=datetime(2026, 8, 15, 10, 0),
            is_published=True,
        ))
        db.session.commit()
        logger.info("COOKING CLASS event seeded.")
    if not Event.query.filter_by(slug="barista-coffee-experience").first():
        db.session.add(Event(
            title="Barista Coffee Experience",
            slug="barista-coffee-experience",
            description="Order from our full Barista menu \u2014 hot drinks, iced drinks, teas and extras \u2014 and pay with MoMo. A live coffee experience by CHERE.",
            summary="Full barista menu with MoMo ordering.",
            event_type="workshop",
            is_paid=False,
            price=0.0,
            currency="RWF",
            location="CHERE Hub, Kigali",
            event_date=datetime(2026, 8, 20, 9, 0),
            is_published=True,
        ))
        db.session.commit()
        logger.info("Barista Coffee Experience event seeded.")
    if not BaristaMenu.query.first():
        menu_items = [
            ("Espresso", "espresso", "Double shot espresso rich and bold", 800, "☕", 1),
            ("Americano", "espresso", "Espresso with hot water", 900, "☕", 2),
            ("Cappuccino", "espresso", "Espresso with steamed milk and foam", 1200, "☕", 3),
            ("Latte", "espresso", "Espresso with lots of steamed milk", 1300, "☕", 4),
            ("Mocha", "espresso", "Espresso with chocolate and steamed milk", 1500, "☕", 5),
            ("Macchiato", "espresso", "Espresso with a spot of foam", 1000, "☕", 6),
            ("Green Tea", "tea", "Fresh green tea", 1000, "🍵", 7),
            ("Black Tea", "tea", "Classic black tea", 1000, "🍵", 8),
            ("Croissant", "pastry", "Buttery, flaky pastry", 800, "🥐", 9),
            ("Pain au Chocolat", "pastry", "Chocolate-filled pastry", 1000, "🥐", 10),
        ]
        for name, category, description, price, icon, order in menu_items:
            db.session.add(BaristaMenu(
                name=name,
                category=category,
                description=description,
                price=price,
                icon=icon,
                order=order,
                is_available=True,
            ))
        db.session.commit()
        logger.info("Barista menu seeded.")


_bootstrap_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
