"""
Script d'initialisation de la base de données CHERE.
Crée les tables, les rôles, un compte administrateur et des données de démonstration.

Usage :
    python seed.py
"""
import os
from app import create_app, db
from app.models import (
    Role, User, Sector, PillarIcon, Service, Project, Partner,
    Statistic, Article, TeamMember
)

app = create_app(os.getenv("FLASK_CONFIG", "development"))


def run():
    with app.app_context():
        db.create_all()

        # --- Rôles ---
        if not Role.query.filter_by(name="admin").first():
            db.session.add(Role(name="admin"))
        if not Role.query.filter_by(name="editor").first():
            db.session.add(Role(name="editor"))
        db.session.commit()

        # --- Compte administrateur par défaut ---
        admin_role = Role.query.filter_by(name="admin").first()
        if not User.query.filter_by(email="admin@chere-global.org").first():
            admin = User(
                full_name="CHERE Administrator",
                email="admin@chere-global.org",
                role_id=admin_role.id,
            )
            admin.set_password("ChangeMe123!")
            db.session.add(admin)

        # --- Statistiques d'impact ---
        if Statistic.query.count() == 0:
            stats = [
                ("Countries", 45, "+", "bi-flag"),
                ("Projects", 120, "+", "bi-kanban"),
                ("Communities", 300, "+", "bi-people"),
                ("Volunteers", 5000, "+", "bi-person-heart"),
                ("Innovations", 60, "+", "bi-lightbulb"),
                ("Renewable Energy Projects", 35, "+", "bi-lightning-charge"),
                ("Humanitarian Missions", 80, "+", "bi-heart"),
                ("People Empowered", 200000, "+", "bi-emoji-smile"),
            ]
            for i, (label, val, suffix, icon) in enumerate(stats):
                db.session.add(Statistic(label=label, value=val, suffix=suffix, icon=icon, order=i))

        # --- Secteurs ---
        if Sector.query.count() == 0:
            sectors = [
                ("Agriculture", "bi-flower1"), ("Tourisme", "bi-airplane"), ("Éducation", "bi-mortarboard"),
                ("Business", "bi-briefcase"), ("Technologie", "bi-cpu"), ("Santé", "bi-heart-pulse"),
                ("Énergie renouvelable", "bi-lightning-charge"), ("Environnement", "bi-tree"),
                ("Humanitaire", "bi-hand-holding-heart"), ("Construction", "bi-building"),
                ("Finance", "bi-cash-coin"), ("Transport", "bi-truck"),
            ]
            for i, (name, icon) in enumerate(sectors):
                slug = name.lower().replace(" ", "-").replace("é", "e")
                db.session.add(Sector(
                    name=name, slug=slug, icon=icon, order=i,
                    short_description="Solutions durables et innovantes déployées à l'échelle mondiale."
                ))

        # --- Icônes des piliers ---
        if PillarIcon.query.count() == 0:
            pillar_data = {
                "innovation": [
                    ("Intelligence Artificielle", "bi-robot"), ("Robotique", "bi-cpu-fill"),
                    ("Cloud Computing", "bi-cloud"), ("R&D", "bi-flask"), ("IoT", "bi-broadcast"),
                    ("Blockchain", "bi-link-45deg"), ("Cybersécurité", "bi-shield-lock"), ("Big Data", "bi-bar-chart"),
                ],
                "renewable": [
                    ("Solaire", "bi-sun"), ("Éolien", "bi-wind"), ("Hydroélectrique", "bi-droplet"),
                    ("Hydrogène vert", "bi-fire"), ("Stockage", "bi-battery-charging"),
                    ("Mobilité électrique", "bi-ev-front"), ("Mini-réseaux", "bi-diagram-3"), ("Villes vertes", "bi-tree"),
                ],
                "humanitarian": [
                    ("Santé", "bi-heart-pulse"), ("Éducation", "bi-mortarboard"), ("Eau", "bi-droplet-half"),
                    ("Urgence", "bi-life-preserver"), ("Femmes", "bi-gender-female"), ("Enfants", "bi-emoji-smile"),
                    ("Réfugiés", "bi-house-heart"), ("Droits humains", "bi-hand-thumbs-up"),
                ],
            }
            for pillar, items in pillar_data.items():
                for i, (label, icon) in enumerate(items):
                    db.session.add(PillarIcon(pillar=pillar, label=label, icon=icon, order=i))

        # --- Projets de démonstration ---
        if Project.query.count() == 0:
            projects = [
                ("Solar Mini-Grid Network — West Africa", "Sénégal", "Africa", 14.5, -14.5, "ongoing", "renewable"),
                ("Digital Skills Academy — Southeast Asia", "Vietnam", "Asia", 14.06, 108.3, "ongoing", "innovation"),
                ("Emergency Water Access — Middle East", "Jordanie", "Asia", 31.24, 36.5, "completed", "humanitarian"),
                ("Climate Resilience Hub — South America", "Brésil", "Americas", -14.2, -51.9, "coming_soon", "renewable"),
                ("Smart Agriculture Initiative — Europe", "France", "Europe", 46.2, 2.2, "coming_soon", "innovation"),
                ("Refugee Support Program — Global", "Multi-pays", "Africa", 9.1, 8.7, "coming_soon", "humanitarian"),
            ]
            for title, country, continent, lat, lng, status, pillar in projects:
                slug = title.lower().replace(" ", "-").replace("—", "-").replace("--", "-")
                db.session.add(Project(
                    title=title, slug=slug, country=country, continent=continent,
                    latitude=lat, longitude=lng, status=status, pillar=pillar,
                    summary="Un projet CHERE conçu pour un impact durable et mesurable.",
                    is_published=True,
                ))

        # --- Partenaires ---
        if Partner.query.count() == 0:
            partners = [
                ("United Nations", "Institution"), ("Global NGOs Alliance", "ONG"),
                ("International University Network", "Université"), ("Green Enterprises Group", "Entreprise"),
                ("World Development Institute", "Institution"), ("Development Finance Bank", "Banque"),
            ]
            for i, (name, category) in enumerate(partners):
                db.session.add(Partner(name=name, category=category, order=i))

        db.session.commit()
        print("Base de données CHERE initialisée avec succès.")
        print("   Compte admin : admin@chere-global.org / ChangeMe123!")
        print("   Pensez à changer ce mot de passe en production.")


if __name__ == "__main__":
    run()
