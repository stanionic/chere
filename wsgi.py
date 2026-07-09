
import os
from app import create_app, db
from app.models import User  # Import models so they're registered
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config_name = os.getenv("FLASK_CONFIG", "development")
app = create_app(config_name=config_name)


def initialize_database():
    """Initialize the database."""
    try:
        logger.info("Initializing database...")
        with app.app_context():
            db.create_all()
            logger.info("Database tables created.")
            
            # Check if admin user exists, if not, create it
            if not User.query.filter_by(email="admin@chere-global.org").first():
                from seed import create_admin
                create_admin()
                logger.info("Admin user created.")
    except Exception as e:
        logger.exception("Error initializing database: %s", str(e))


# Initialize database immediately when wsgi.py is loaded
initialize_database()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
