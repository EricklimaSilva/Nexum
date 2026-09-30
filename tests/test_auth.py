from werkzeug.security import check_password_hash

from app.auth.models import User
from app.auth.services import create_user, get_user_by_email
from app.extensions import db
from tests.helpers import assert_redirect_to_login


def test_register_valid_creates_user_profile_and_progress(app, client):
    response = client.post(
        "/auth/register",
        data={
            "email": "novo@example.com",
            "password": "Pass1234",
            "name": "Novo Usuário",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    user = get_user_by_email("novo@example.com")
    assert user is not None
    assert user.profile is not None
    assert user.profile.name == "Novo Usuário"
    assert user.progress is not None
    assert user.progress.total_xp == 0
    assert user.progress.level == 1
    assert user.progress.rank == "E"


def test_register_duplicate_email_does_not_create_second_user(app, client):
    create_user("duplicado@example.com", "Pass1234", "Usuário")

    response = client.post(
        "/auth/register",
        data={
            "email": "duplicado@example.com",
            "password": "Pass1234",
            "name": "Outro Usuário",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert db.session.query(User).filter_by(email="duplicado@example.com").count() == 1


def test_register_invalid_email_rejected(app, client):
    response = client.post(
        "/auth/register",
        data={
            "email": "email-invalido",
            "password": "Pass1234",
            "name": "Teste",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert db.session.query(User).filter_by(email="email-invalido").count() == 0


def test_login_valid_redirects_to_dashboard(app, client, user):
    response = client.post(
        "/auth/login",
        data={"email": user.email, "password": "Pass1234"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_login_with_wrong_password_is_rejected(app, client, user):
    response = client.post(
        "/auth/login",
        data={"email": user.email, "password": "SenhaErrada"},
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"Credenciais inv" in response.data


def test_logout_redirects_to_login(app, client, user):
    client.post(
        "/auth/login",
        data={"email": user.email, "password": "Pass1234"},
        follow_redirects=False,
    )

    response = client.get("/auth/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")


def test_protected_route_requires_auth(app, client):
    response = client.get("/", follow_redirects=False)

    assert_redirect_to_login(response)


def test_password_is_hashed_not_plain_text(app, user):
    assert user.password_hash != "Pass1234"
    assert user.password_hash != ""
    assert check_password_hash(user.password_hash, "Pass1234") is True
