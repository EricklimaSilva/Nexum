import pytest
from sqlalchemy import text

from app.auth.models import User
from app.auth.services import create_user
from app.extensions import db
from app.progression.models import XPEvent
from app.progression.services import award_xp_for_event, create_initial_progress, get_user_progress
from app.quick_log.models import QuickLog
from app.quick_log.services import create_quick_log


@pytest.mark.postgres
def test_postgres_database_target_is_exactly_nexum_test(postgres_app):
    with postgres_app.app_context():
        db_name = db.session.execute(text("SELECT current_database()"))
        assert db_name.scalar() == "nexum_test"


@pytest.mark.postgres
def test_xp_event_is_unique_and_idempotent(postgres_app):
    with postgres_app.app_context():
        user = create_user("pgxp@example.com", "Pass1234", "PG XP")
        create_initial_progress(user)
        db.session.commit()

        first = award_xp_for_event(user, "quick_log", 99, 15, "study milestone")
        second = award_xp_for_event(user, "quick_log", 99, 15, "study milestone")

        assert first.id == second.id
        assert db.session.query(XPEvent).filter_by(user_id=user.id).count() == 1
        assert get_user_progress(user).total_xp == 15


@pytest.mark.postgres
def test_atomic_rollback_preserves_xp_and_removes_partial_quick_log(postgres_app):
    with postgres_app.app_context():
        user = create_user("rollback_pg@example.com", "Pass1234", "Rollback PG")
        create_initial_progress(user)
        db.session.commit()
        original_total = get_user_progress(user).total_xp

        try:
            create_quick_log(user, action="Estudei SQL", category="study", xp_awarded=10)
            award_xp_for_event(user, "quick_log", 101, 10, "test")
            raise RuntimeError("rollback now")
        except RuntimeError:
            db.session.rollback()

        assert db.session.query(QuickLog).filter_by(user_id=user.id).count() == 0
        assert db.session.query(XPEvent).filter_by(user_id=user.id).count() == 0
        assert get_user_progress(user).total_xp == original_total


@pytest.mark.postgres
def test_postgres_migration_head_matches_project_head(postgres_app):
    with postgres_app.app_context():
        version = db.session.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
        assert version == "f84b9a4d1e2a"


@pytest.mark.postgres
def test_postgres_user_isolation_and_foreign_keys(postgres_app):
    with postgres_app.app_context():
        user = create_user("iso_pg@example.com", "Pass1234", "User PG")
        create_initial_progress(user)
        db.session.commit()

        quick_log = create_quick_log(user, action="Ação isolada", category="study", xp_awarded=10)
        db.session.commit()

        assert quick_log.user_id == user.id
        assert db.session.query(User).filter_by(id=user.id).count() == 1
        assert db.session.query(QuickLog).filter_by(user_id=user.id).count() == 1
