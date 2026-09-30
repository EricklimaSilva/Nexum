import pytest

from app.extensions import db
from app.workouts.services import (
    add_workout_exercise,
    add_workout_set,
    create_workout_session,
    get_workout_session_for_user,
    list_workout_sessions_for_user,
)


def test_create_session_and_exercise(app, user):
    session = create_workout_session(user, name="Treino A", notes="Treino de força")
    db.session.flush()
    exercise = add_workout_exercise(user, session_id=session.id, name="Supino", category="push")
    db.session.flush()

    assert session.user_id == user.id
    assert exercise.session_id == session.id
    assert exercise.category == "push"


def test_set_creation_requires_reps_or_duration(app, user):
    session = create_workout_session(user, name="Treino B")
    db.session.flush()
    exercise = add_workout_exercise(user, session_id=session.id, name="Agachamento", category="legs")
    db.session.flush()

    workout_set = add_workout_set(user, exercise_id=exercise.id, reps=8)
    assert workout_set.reps == 8

    with pytest.raises(ValueError):
        add_workout_set(user, exercise_id=exercise.id, reps=None, duration_seconds=None)


def test_invalid_exercise_category_is_rejected(app, user):
    session = create_workout_session(user, name="Treino C")
    db.session.flush()

    with pytest.raises(ValueError):
        add_workout_exercise(user, session_id=session.id, name="Exercício inválido", category="invalido")


def test_workout_session_history_and_isolation(app, user, second_user):
    session_a = create_workout_session(user, name="Treino do usuário A")
    db.session.flush()
    session_b = create_workout_session(second_user, name="Treino do usuário B")
    db.session.flush()

    sessions_a = list_workout_sessions_for_user(user, limit=20)
    sessions_b = list_workout_sessions_for_user(second_user, limit=20)

    assert session_a.id in {item.id for item in sessions_a}
    assert session_b.id in {item.id for item in sessions_b}
    assert session_a.id not in {item.id for item in sessions_b}


def test_cross_user_lookup_rejected_for_workout_session(app, user, second_user):
    session = create_workout_session(user, name="Sessão de usuário A")
    db.session.flush()

    with pytest.raises(RuntimeError):
        get_workout_session_for_user(second_user, session.id)
