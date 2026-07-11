"""Seeder pour initialiser les données de base de l'application CHERE."""
import os
from app import create_app, db
from app.models import (
    User, Role, Sector, PillarIcon, Service, Project,
    Partner, TeamMember, Article, Statistic
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


def run():
    print(f"DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
    with app.app_context():
        db.create_all()
        seed_roles()
        seed_admin()
        seed_statistics()
        seed_sectors()
        seed_pillar_icons()
        print("[OK] Seed termine.")


if __name__ == "__main__":
    run()
