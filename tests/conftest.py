import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.auth.services import create_user
from app.config import TestingConfig
from app.extensions import db


def assert_safe_test_database(app):
    if app.config.get("TESTING") is not True:
        raise RuntimeError(
            f"TEST SAFETY ABORT: app.config['TESTING'] is not True for app {app.name}."
        )

    with app.app_context():
        url = db.engine.url

    backend_name = url.get_backend_name()
    database_name = (url.database or "").lower()
    url_text = str(url).lower()

    if backend_name != "sqlite":
        raise RuntimeError(
            f"TEST SAFETY ABORT: pytest tentou usar banco não-SQLite: {url}"
        )

    if (
        "postgresql" in url_text
        or "psycopg" in url_text
        or database_name in {"nexum", "nexum_recovered", "nexum_test"}
    ):
        raise RuntimeError(
            f"TEST SAFETY ABORT: pytest foi bloqueado antes de acessar um banco de desenvolvimento/produção: {url}"
        )

    return url


def assert_safe_postgres_test_database(app):
    if app.config.get("TESTING") is not True:
        raise RuntimeError(
            f"TEST SAFETY ABORT: app.config['TESTING'] is not True for postgres app {app.name}."
        )

    with app.app_context():
        url = db.engine.url

    backend_name = url.get_backend_name()
    database_name = (url.database or "").lower()
    url_text = str(url).lower()

    if backend_name != "postgresql":
        raise RuntimeError(
            f"TEST SAFETY ABORT: postgres test attempted to use a non-PostgreSQL backend: {url}"
        )

    if database_name != "nexum_test":
        raise RuntimeError(
            f"TEST SAFETY ABORT: postgres integration must target the exact database nexum_test. Received: {database_name}"
        )

    forbidden = {"nexum", "nexum_recovered"}
    if database_name in forbidden or "nexum_recovered" in url_text or "nexum" in url_text and "nexum_test" not in url_text:
        raise RuntimeError(
            f"TEST SAFETY ABORT: postgres integration blocked for forbidden database: {url}"
        )

    return url


@pytest.fixture()
def app():
    app = create_app(TestingConfig)

    assert_safe_test_database(app)

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def postgres_app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://erick@localhost:5433/nexum_test",
    })

    assert_safe_postgres_test_database(app)

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def db_session(app):
    with app.app_context():
        yield db.session


@pytest.fixture()
def user(app):
    return create_user("user@example.com", "Pass1234", "Usuário Teste")


@pytest.fixture()
def second_user(app):
    return create_user("second@example.com", "Pass1234", "Segundo Usuário")


@pytest.fixture()
def authenticated_client(app, client, user):
    with app.app_context():
        response = client.post(
            "/auth/login",
            data={"email": user.email, "password": "Pass1234"},
            follow_redirects=False,
        )
    assert response.status_code == 302
    yield client
