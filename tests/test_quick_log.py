import pytest

from app.extensions import db
from app.quick_log.models import QuickLog
from app.quick_log.services import create_quick_log, list_quick_logs_for_user
from tests.helpers import assert_redirect_to_login


def test_quick_log_route_requires_auth(client):
    response = client.get("/quick-log/", follow_redirects=False)
    assert_redirect_to_login(response)


def test_quick_log_index_for_authenticated_user(authenticated_client, user):
    response = authenticated_client.get("/quick-log/", follow_redirects=False)

    assert response.status_code == 200
    assert b"Registro r" in response.data or b"Quick Log" in response.data


def test_create_valid_quick_log_persists_and_awards_xp(authenticated_client, user):
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "Estudei SQL por 1 hora", "category": "study"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    log = QuickLog.query.filter_by(user_id=user.id).first()
    assert log is not None
    assert log.action == "Estudei SQL por 1 hora"
    assert log.category == "study"
    assert log.xp_awarded == 10
    assert user.progress.total_xp == 10


def test_blank_action_is_rejected(authenticated_client, user):
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "   ", "category": "study"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert QuickLog.query.filter_by(user_id=user.id).count() == 0


def test_action_longer_than_160_is_rejected(authenticated_client, user):
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "x" * 161, "category": "study"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert QuickLog.query.filter_by(user_id=user.id).count() == 0


def test_empty_category_is_accepted_and_normalized(authenticated_client, user):
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "Leitura de artigo", "category": "  Study  "},
        follow_redirects=False,
    )

    assert response.status_code == 302
    log = QuickLog.query.filter_by(user_id=user.id).first()
    assert log is not None
    assert log.category == "study"


def test_history_order_is_most_recent_first(authenticated_client, user):
    create_quick_log(user, action="Primeiro", category="study", xp_awarded=10)
    create_quick_log(user, action="Segundo", category="study", xp_awarded=10)

    logs = list_quick_logs_for_user(user, limit=10)
    assert [log.action for log in logs[:2]] == ["Segundo", "Primeiro"]


def test_list_limit_is_20_for_user(authenticated_client, user):
    for index in range(25):
        create_quick_log(user, action=f"Ação {index}", category="study", xp_awarded=10)

    logs = list_quick_logs_for_user(user, limit=20)
    assert len(logs) == 20


def test_user_only_sees_own_quick_logs(authenticated_client, user, second_user):
    create_quick_log(user, action="Ação do usuário A", category="study", xp_awarded=10)
    create_quick_log(second_user, action="Ação do usuário B", category="study", xp_awarded=10)

    logs_user = list_quick_logs_for_user(user, limit=10)
    logs_second = list_quick_logs_for_user(second_user, limit=10)

    assert len(logs_user) == 1
    assert len(logs_second) == 1
    assert logs_user[0].action == "Ação do usuário A"
    assert logs_second[0].action == "Ação do usuário B"


def test_invalid_quick_log_does_not_leave_partial_state(authenticated_client, user):
    before_total = user.progress.total_xp
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "", "category": "study"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert QuickLog.query.filter_by(user_id=user.id).count() == 0
    assert user.progress.total_xp == before_total


def test_quick_log_and_xp_are_persisted_together_in_normal_flow(authenticated_client, user):
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "Concluí milestone", "category": "career"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    log = QuickLog.query.filter_by(user_id=user.id).first()
    assert log is not None
    assert log.xp_awarded == 10
    assert user.progress.total_xp == 10
    assert db.session.query(QuickLog).count() == 1
