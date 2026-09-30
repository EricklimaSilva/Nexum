import pytest

from app import create_app
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
from app.quick_log.models import QuickLog


def test_testing_config_is_sqlite_and_safe():
    app = create_app(TestingConfig)
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite://"


def test_production_config_requires_real_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError):
        ProductionConfig()


def test_login_requires_csrf_when_not_testing():
    app = create_app(DevelopmentConfig)
    client = app.test_client()

    response = client.post(
        "/auth/login",
        data={"email": "user@example.com", "password": "Pass1234"},
        follow_redirects=False,
    )

    assert response.status_code == 400


def test_quick_log_rejects_invalid_category(authenticated_client, user):
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "Estudei SQL", "category": "invalid"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert QuickLog.query.filter_by(user_id=user.id).count() == 0


def test_quick_log_rejects_immediate_duplicate(authenticated_client, user):
    first = authenticated_client.post(
        "/quick-log/",
        data={"action": "Ação repetida", "category": "study"},
        follow_redirects=False,
    )
    second = authenticated_client.post(
        "/quick-log/",
        data={"action": "Ação repetida", "category": "study"},
        follow_redirects=False,
    )

    assert first.status_code == 302
    assert second.status_code == 302
    assert QuickLog.query.filter_by(user_id=user.id, action="Ação repetida").count() == 1
