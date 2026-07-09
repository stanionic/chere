
"""Seeder pour initialiser les données de base de l'application CHERE."""
import os
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User, UserRole

# Créer une instance de l'application (dev par défaut)
config_name = os.getenv("FLASK_CONFIG", "development")
app = create_app(config_name)


def create_admin():
    """Create default admin user."""
    if not User.query.filter_by(email="admin@chere-global.org").first():
        admin_user = User(
            first_name="Admin",
            last_name="CHERE",
            email="admin@chere-global.org",
            role=UserRole.ADMIN,
            password_hash=generate_password_hash("ChangeMe123!"),
            is_active=True,
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin par défaut créé:")
        print("   Email: admin@chere-global.org")
        print("   Mot de passe: ChangeMe123!")
        print("   ⚠️  Changez immédiatement ce mot de passe!")


def run():
    """Run all seed operations."""
    print("Starting seed script...")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    with app.app_context():
        print("Creating all tables...")
        db.create_all()
        print("Tables created.")
        create_admin()


if __name__ == "__main__":
    run()
