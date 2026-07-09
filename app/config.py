
"""Configuration de l'application CHERE (dev / prod / test)."""
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}
    ITEMS_PER_PAGE = 9
    SITE_NAME = "CHERE"
    SITE_TAGLINE = "Community • Humanity • Empowerment • Resources • Environment"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'chere.db')}"
    )
    logger.info(f"DevelopmentConfig using DB: {SQLALCHEMY_DATABASE_URI}")


class ProductionConfig(BaseConfig):
    DEBUG = True  # Still temporarily enabled for troubleshooting
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    logger.info(f"ProductionConfig raw DATABASE_URL: {SQLALCHEMY_DATABASE_URI}")

    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+psycopg2://", 1)
    logger.info(f"ProductionConfig final DB URI: {SQLALCHEMY_DATABASE_URI}")

    # Important: do not raise at import time; validate when app initializes or on first use.
    # This prevents local runs that don't use ProductionConfig from crashing.
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
