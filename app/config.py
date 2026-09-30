import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INSECURE_SECRETS = {
    "dev-secret-key-change-me",
    "test-secret-key",
    "test-secret-key-unsafe-only-for-tests",
}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://localhost:5433/nexum_recovered")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    @classmethod
    def validate(cls):
        return None


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Strict"

    def __new__(cls, *args, **kwargs):
        secret = os.getenv("SECRET_KEY")
        if not secret or secret in DEFAULT_INSECURE_SECRETS:
            raise ValueError("ProductionConfig requires a non-default SECRET_KEY.")
        return super().__new__(cls)

    @classmethod
    def validate(cls):
        secret = os.getenv("SECRET_KEY")
        if not secret or secret in DEFAULT_INSECURE_SECRETS:
            raise ValueError("ProductionConfig requires a non-default SECRET_KEY.")
        return None


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-unsafe-only-for-tests"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
