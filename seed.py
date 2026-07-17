"""Seeder pour initialiser les données de base de l'application CHERE."""
import os
from datetime import datetime
from app import create_app, db
from app.models import (
    User, Role, Sector, PillarIcon, Service, Project,
    Partner, TeamMember, Article, Statistic, BaristaMenu,
    Event, Category, Product, ProductVariant, Merchant, Shop
)

config_name = os.getenv("FLASK_CONFIG", "development")
app = create_app(config_name)


def seed_roles():
    for name in ("admin", "editor", "viewer"):
        if not Role.query.filter_by(name=name).first():
            db.session.add(Role(name=name))
    db.session.commit()


def seed_admin():
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        db.session.add(Role(name="admin"))
        db.session.commit()
        admin_role = Role.query.filter_by(name="admin").first()

    user = User.query.filter_by(email="ADMIN-CHERE").first()
    if not user:
        user = User.query.filter_by(email="admin@chere-global.org").first()
    if not user:
        user = User(full_name="Admin CHERE", email="ADMIN-CHERE", role_id=admin_role.id)
    else:
        user.email = "ADMIN-CHERE"
        user.full_name = "Admin CHERE"
        user.role_id = admin_role.id

    user.set_password("Stan-Chere.Admin..Good")
    db.session.add(user)
    db.session.commit()
    print("[OK] Admin cree - Email: ADMIN-CHERE / MDP: Stan-Chere.Admin..Good")


def seed_statistics():
    if Statistic.query.count():
        return
    stats = [
        ("Countries", 45, "+", "bi-globe", 1),
        ("Projects", 120, "+", "bi-folder-check", 2),
        ("People Empowered", 500000, "+", "bi-people-fill", 3),
        ("Partners", 80, "+", "bi-handshake", 4),
    ]
    for label, value, suffix, icon, order in stats:
        db.session.add(Statistic(label=label, value=value, suffix=suffix, icon=icon, order=order))
    db.session.commit()


def seed_sectors():
    if Sector.query.count():
        return
    sectors = [
        ("Agriculture", "agriculture", "bi-tree", "Développement agricole durable"),
        ("Santé", "sante", "bi-heart-pulse", "Accès aux soins de santé"),
        ("Technologie", "technologie", "bi-cpu", "Innovation technologique"),
        ("Éducation", "education", "bi-book", "Accès à l'éducation"),
        ("Énergie", "energie", "bi-lightning-charge", "Énergies renouvelables"),
        ("Eau", "eau", "bi-droplet", "Accès à l'eau potable"),
    ]
    for i, (name, slug, icon, desc) in enumerate(sectors):
        db.session.add(Sector(name=name, slug=slug, icon=icon, short_description=desc, order=i))
    db.session.commit()


def seed_pillar_icons():
    if PillarIcon.query.count():
        return
    icons = [
        ("innovation", "IA & Big Data", "bi-robot", 1),
        ("innovation", "Blockchain", "bi-link-45deg", 2),
        ("innovation", "IoT", "bi-wifi", 3),
        ("innovation", "Drones", "bi-send", 4),
        ("renewable", "Solaire", "bi-sun", 1),
        ("renewable", "Éolien", "bi-wind", 2),
        ("renewable", "Hydraulique", "bi-water", 3),
        ("renewable", "Biomasse", "bi-tree", 4),
        ("humanitarian", "Aide d'urgence", "bi-heart", 1),
        ("humanitarian", "Réfugiés", "bi-house-heart", 2),
        ("humanitarian", "Nutrition", "bi-egg-fried", 3),
        ("humanitarian", "Éducation", "bi-book", 4),
    ]
    for pillar, label, icon, order in icons:
        db.session.add(PillarIcon(pillar=pillar, label=label, icon=icon, order=order))
    db.session.commit()


def seed_barista_menu():
    if BaristaMenu.query.count():
        return
    menu = [
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
    for name, category, description, price, icon, order in menu:
        db.session.add(BaristaMenu(
            name=name, category=category, description=description,
            price=price, icon=icon, order=order, is_available=True
        ))
    db.session.commit()


def seed_events():
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
    if not Event.query.filter_by(slug="barista-coffee-experience").first():
        db.session.add(Event(
            title="Barista Coffee Experience",
            slug="barista-coffee-experience",
            description="Order from our full Barista menu, enjoy live coffee service, and pay with MoMo as part of the CHERE experience.",
            summary="Full barista menu with MoMo ordering.",
            event_type="barista",
            is_paid=False,
            price=0.0,
            currency="RWF",
            location="CHERE Hub, Kigali",
            event_date=datetime(2026, 8, 20, 9, 0),
            is_published=True,
        ))
    db.session.commit()


def run():
    print(f"DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
    with app.app_context():
        db.create_all()
        seed_roles()
        seed_admin()
        seed_statistics()
        seed_sectors()
        seed_pillar_icons()
        seed_events()
        seed_barista_menu()
        print("[OK] Seed termine.")


if __name__ == "__main__":
    run()
