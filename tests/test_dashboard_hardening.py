import pytest

from app.extensions import db
from app.goals.models import Goal
from app.quick_log.models import QuickLog


def test_dashboard_requires_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_dashboard_summary_for_authenticated_user(authenticated_client, user):
    response = authenticated_client.get("/", follow_redirects=False)

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "dashboard" in html.lower()
    assert "Usuário Teste" in html or "Usuário" in html


def test_dashboard_reflects_quick_log_xp_and_progress(authenticated_client, user):
    authenticated_client.post(
        "/quick-log/",
        data={"action": "Estudei SQL", "category": "study"},
        follow_redirects=False,
    )

    response = authenticated_client.get("/", follow_redirects=False)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "10" in html
    assert "level" in html.lower()
    assert "xp" in html.lower()
    assert QuickLog.query.filter_by(user_id=user.id).count() == 1


def test_dashboard_handles_user_without_activity(authenticated_client, user):
    response = authenticated_client.get("/", follow_redirects=False)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "0" in html


def test_quick_log_action_is_normalized_for_duplicate_detection(authenticated_client, user):
    first = authenticated_client.post(
        "/quick-log/",
        data={"action": "  Estudei SQL  ", "category": "study"},
        follow_redirects=False,
    )
    second = authenticated_client.post(
        "/quick-log/",
        data={"action": "estudei sql", "category": "study"},
        follow_redirects=False,
    )

    assert first.status_code == 302
    assert second.status_code == 302
    assert QuickLog.query.filter_by(user_id=user.id).count() == 1


def test_quick_log_rejects_invalid_category_and_returns_clean_error(authenticated_client, user):
    response = authenticated_client.post(
        "/quick-log/",
        data={"action": "Leitura de artigo", "category": "invalid-category"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert QuickLog.query.filter_by(user_id=user.id).count() == 0


def test_quick_log_rate_limit_is_enforced_per_user(authenticated_client, user):
    response = None
    for index in range(21):
        response = authenticated_client.post(
            "/quick-log/",
            data={"action": f"Ação {index} única", "category": "study"},
            follow_redirects=False,
        )

    assert response.status_code == 429


def test_body_routes_update_profile_and_measurement(authenticated_client, user):
    profile_response = authenticated_client.post(
        "/body/profile",
        data={"height_cm": "175.50"},
        follow_redirects=False,
    )
    measurement_response = authenticated_client.post(
        "/body/measurement",
        data={"weight_kg": "70.00"},
        follow_redirects=False,
    )

    assert profile_response.status_code == 302
    assert measurement_response.status_code == 302

    index_response = authenticated_client.get("/body/", follow_redirects=False)
    assert index_response.status_code == 200


def test_goals_routes_create_update_and_complete(authenticated_client, user):
    create_response = authenticated_client.post(
        "/goals/",
        data={"title": "Meta de estudo", "description": "Ler 3 capítulos", "category": "study"},
        follow_redirects=False,
    )
    assert create_response.status_code == 302

    goal = Goal.query.filter_by(user_id=user.id).first()
    assert goal is not None

    progress_response = authenticated_client.post(
        f"/goals/{goal.id}/progress",
        data={"progress_percent": "25"},
        follow_redirects=False,
    )
    complete_response = authenticated_client.post(
        f"/goals/{goal.id}/complete",
        follow_redirects=False,
    )

    assert progress_response.status_code == 302
    assert complete_response.status_code == 302
    assert db.session.get(Goal, goal.id).status == "completed"


def test_finance_routes_update_settings_and_manage_commitment(authenticated_client, user):
    settings_response = authenticated_client.post(
        "/finance/settings",
        data={
            "current_balance": "2500.00",
            "protected_savings": "200.00",
            "payday_first": "10",
            "payday_second": "20",
        },
        follow_redirects=False,
    )
    commitment_response = authenticated_client.post(
        "/finance/commitment",
        data={
            "name": "Internet",
            "amount": "120.50",
            "due_date": "2026-12-15",
            "kind": "fixed",
        },
        follow_redirects=False,
    )

    assert settings_response.status_code == 302
    assert commitment_response.status_code == 302

    commitment = user.finance_commitments[0]
    toggle_response = authenticated_client.post(
        f"/finance/commitment/{commitment.id}/toggle-paid",
        follow_redirects=False,
    )
    delete_response = authenticated_client.post(
        f"/finance/commitment/{commitment.id}/delete",
        follow_redirects=False,
    )

    assert toggle_response.status_code == 302
    assert delete_response.status_code == 302

    finance_index = authenticated_client.get("/finance/", follow_redirects=False)
    assert finance_index.status_code == 200


def test_workouts_routes_create_session_exercise_and_set(authenticated_client, user):
    session_response = authenticated_client.post(
        "/workouts/session",
        data={"name": "Treino de força", "notes": "Supino e agachamento"},
        follow_redirects=False,
    )
    assert session_response.status_code == 302

    session_id = user.workout_sessions[0].id
    exercise_response = authenticated_client.post(
        f"/workouts/session/{session_id}/exercise",
        data={"name": "Supino", "category": "push"},
        follow_redirects=False,
    )
    assert exercise_response.status_code == 302

    exercise = user.workout_sessions[0].exercises[0]
    set_response = authenticated_client.post(
        f"/workouts/exercise/{exercise.id}/set",
        data={"reps": "8", "duration_seconds": ""},
        follow_redirects=False,
    )

    assert set_response.status_code == 302
    index_response = authenticated_client.get("/workouts/?session_id={session_id}", follow_redirects=False)
    assert index_response.status_code == 200
