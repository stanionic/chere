"""Configuration de l'application CHERE (dev / prod / test)."""
import os
from dotenv import load_dotenv

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


class ProductionConfig(BaseConfig):
    DEBUG = False

    @classmethod
    def _get_db_uri(cls):
        uri = os.environ.get("DATABASE_URL", "")
        if uri.startswith("postgresql://"):
            uri = uri.replace("postgresql://", "postgresql+psycopg2://", 1)
        return uri

    SQLALCHEMY_DATABASE_URI = property(lambda self: ProductionConfig._get_db_uri())

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# Resolve SQLALCHEMY_DATABASE_URI at instantiation time for ProductionConfig
_prod_uri = os.environ.get("DATABASE_URL", "")
if _prod_uri.startswith("postgresql://"):
    _prod_uri = _prod_uri.replace("postgresql://", "postgresql+psycopg2://", 1)
ProductionConfig.SQLALCHEMY_DATABASE_URI = _prod_uri


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
