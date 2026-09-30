import pytest

from app.extensions import db
from app.goals.models import GOAL_CATEGORIES
from app.goals.services import (
    complete_goal,
    create_goal,
    get_goal_for_user,
    list_goals_for_user,
    update_goal_progress,
)


def test_create_goal_success(app, user):
    goal = create_goal(
        user,
        title="Estudar para prova",
        description="Estudar 2h por dia",
        category="study",
    )
    db.session.flush()

    assert goal.user_id == user.id
    assert goal.title == "Estudar para prova"
    assert goal.status == "active"
    assert goal.progress_percent == 0


def test_create_goal_requires_title(app, user):
    with pytest.raises(ValueError):
        create_goal(user, title="   ")


def test_goal_category_validation(app, user):
    create_goal(user, title="Meta válida", category="personal")

    with pytest.raises(ValueError):
        create_goal(user, title="Categoria inválida", category="invalida")

    assert "personal" in GOAL_CATEGORIES


def test_update_goal_progress_validates_ranges(app, user):
    goal = create_goal(user, title="Meta progressiva")
    db.session.flush()

    updated = update_goal_progress(user, goal_id=goal.id, progress_percent=25)
    assert updated.progress_percent == 25

    with pytest.raises(ValueError):
        update_goal_progress(user, goal_id=goal.id, progress_percent=100)

    with pytest.raises(ValueError):
        update_goal_progress(user, goal_id=goal.id, progress_percent=-1)


def test_complete_goal_sets_completed_state(app, user):
    goal = create_goal(user, title="Meta concluída")
    db.session.flush()

    completed = complete_goal(user, goal_id=goal.id)

    assert completed.status == "completed"
    assert completed.progress_percent == 100
    assert completed.completed_at is not None


def test_user_cannot_access_other_users_goal(app, user, second_user):
    goal = create_goal(user, title="Meta do usuário A")
    db.session.flush()

    with pytest.raises(RuntimeError):
        get_goal_for_user(second_user, goal.id)

    assert list_goals_for_user(user, status="active")[0].id == goal.id
    assert list_goals_for_user(second_user, status="active") == []
