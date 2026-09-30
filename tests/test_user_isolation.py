import pytest

from app.body.services import add_body_measurement, upsert_body_profile
from app.finance.services import create_commitment, get_commitment_for_user
from app.goals.services import create_goal, get_goal_for_user
from app.quick_log.services import create_quick_log
from app.workouts.services import create_workout_session, get_workout_session_for_user


def test_cross_user_idor_is_blocked_across_modules(app, user, second_user):
    goal = create_goal(user, title="Meta do Usuário A")
    commitment = create_commitment(
        user,
        name="Compromisso A",
        amount="100.00",
        due_date="2026-12-10",
        kind="fixed",
        is_paid=False,
    )
    profile = upsert_body_profile(user, height_cm="170.00")
    measurement = add_body_measurement(user, weight_kg="68.00")
    session = create_workout_session(user, name="Sessão do usuário A")
    quick_log = create_quick_log(user, action="Ação do usuário A", category="study", xp_awarded=10)

    with pytest.raises(RuntimeError):
        get_goal_for_user(second_user, goal.id)

    with pytest.raises(RuntimeError):
        get_commitment_for_user(second_user, commitment.id)

    assert profile.user_id == user.id
    assert measurement.user_id == user.id

    with pytest.raises(RuntimeError):
        get_workout_session_for_user(second_user, session.id)

    logs = [item.action for item in user.quick_logs]
    assert quick_log.action in logs
    assert quick_log.user_id == user.id
