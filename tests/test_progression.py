import pytest

from app.auth.services import create_user
from app.extensions import db
from app.progression.services import (
    add_xp,
    calculate_level,
    calculate_rank,
    cumulative_xp_before_level,
    create_initial_progress,
    get_user_progress,
    sync_progress,
    xp_for_next_level,
)


def test_calculate_level_boundaries(app):
    assert calculate_level(0) == 1
    assert calculate_level(99) == 1
    assert calculate_level(100) == 2
    assert calculate_level(249) == 2
    assert calculate_level(250) == 3
    assert calculate_level(449) == 3
    assert calculate_level(450) == 4


def test_calculate_rank_boundaries(app):
    assert calculate_rank(1) == "E"
    assert calculate_rank(4) == "E"
    assert calculate_rank(5) == "D"
    assert calculate_rank(9) == "D"
    assert calculate_rank(10) == "C"
    assert calculate_rank(20) == "B"
    assert calculate_rank(35) == "A"
    assert calculate_rank(49) == "A"
    assert calculate_rank(50) == "S"


def test_xp_helpers_and_level_math(app):
    assert xp_for_next_level(1) == 100
    assert xp_for_next_level(2) == 150
    assert xp_for_next_level(3) == 200
    assert cumulative_xp_before_level(1) == 0
    assert cumulative_xp_before_level(2) == 100
    assert cumulative_xp_before_level(3) == 250
    assert cumulative_xp_before_level(4) == 450


def test_create_initial_progress_for_user(app):
    user = create_user("progress@example.com", "Pass1234", "Progress User")
    progress = create_initial_progress(user)

    assert progress.user_id == user.id
    assert progress.total_xp == 0
    assert progress.level == 1
    assert progress.rank == "E"


def test_add_xp_increments_total_and_updates_level(app):
    user = create_user("xp@example.com", "Pass1234", "XP User")

    add_xp(user, 150)
    progress = get_user_progress(user)

    assert progress.total_xp == 150
    assert progress.level == 2
    assert progress.rank == "E"


def test_add_xp_rejects_negative_bool_and_invalid_input(app):
    user = create_user("badxp@example.com", "Pass1234", "Bad XP")

    with pytest.raises(ValueError):
        add_xp(user, -1)

    with pytest.raises(ValueError):
        add_xp(user, True)

    with pytest.raises(ValueError):
        add_xp(user, "abc")

    assert get_user_progress(user).total_xp == 0


def test_sync_progress_updates_level_and_rank(app):
    user = create_user("sync@example.com", "Pass1234", "Sync User")
    progress = get_user_progress(user)
    progress.total_xp = 750

    sync_progress(progress)

    assert progress.level == 5
    assert progress.rank == "D"


def test_rollback_restores_previous_progress_state(app):
    user = create_user("rollback@example.com", "Pass1234", "Rollback User")
    progress = get_user_progress(user)
    original_total = progress.total_xp

    with app.app_context():
        progress.total_xp = 999
        db.session.flush()
        db.session.rollback()
        db.session.expire_all()
        reloaded = db.session.get(type(progress), progress.id)

    assert reloaded.total_xp == original_total
