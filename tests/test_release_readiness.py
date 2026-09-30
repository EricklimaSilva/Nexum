from app import create_app
from app.config import TestingConfig


def test_create_app_default_works():
    app = create_app()
    assert app is not None
    assert app.config.get("TESTING") is False
    assert "nexum_recovered" in app.config.get("SQLALCHEMY_DATABASE_URI", "")


def test_create_app_testing_config_works():
    app = create_app(TestingConfig)
    assert app is not None
    assert app.config.get("TESTING") is True
    assert app.config.get("SQLALCHEMY_DATABASE_URI") == "sqlite://"


def test_health_endpoint_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_security_headers_are_present(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_auth_pages_render(client):
    login = client.get("/auth/login")
    register = client.get("/auth/register")

    assert login.status_code == 200
    assert register.status_code == 200


def test_protected_routes_redirect_anonymous_user(client):
    response = client.get("/")
    assert response.status_code == 302

    finance_response = client.get("/finance/")
    assert finance_response.status_code == 302


def test_main_templates_load(client):
    pages = [
        "/auth/login",
        "/auth/register",
        "/quick-log/",
        "/goals/",
        "/finance/",
        "/body/",
        "/workouts/",
    ]

    for path in pages:
        response = client.get(path, follow_redirects=False)
        assert response.status_code in {200, 302}
