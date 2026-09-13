from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.body.services import get_body_status_for_user
from app.finance.services import calculate_safe_spend
from app.goals.services import list_goals_for_user
from app.workouts.services import list_workout_sessions_for_user
from app.progression.services import (
    get_progress_percentage,
    get_user_progress,
    get_xp_for_current_level,
    get_xp_needed_for_next_level,
)


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")


@dashboard_bp.route("/")
@login_required
def index():
    progress = get_user_progress(current_user)
    xp_current = get_xp_for_current_level(progress.total_xp, progress.level)
    xp_next = get_xp_needed_for_next_level(progress.total_xp, progress.level)
    progress_percent = get_progress_percentage(progress.total_xp, progress.level)

    finance_summary = None
    if getattr(current_user, "finance_settings", None) is not None:
        finance_summary = calculate_safe_spend(current_user)

    body_status = get_body_status_for_user(current_user)
    recent_workouts = list_workout_sessions_for_user(current_user, limit=1)
    latest_workout = recent_workouts[0] if recent_workouts else None

    active_goals = list_goals_for_user(current_user, status="active")
    completed_goals = list_goals_for_user(current_user, status="completed")
    featured_goal = active_goals[0] if active_goals else None

    return render_template(
        "dashboard/index.html",
        progress=progress,
        xp_current=xp_current,
        xp_next=xp_next,
        progress_percent=progress_percent,
        user_name=current_user.profile.name,
        finance_summary=finance_summary,
        body_status=body_status,
        latest_workout=latest_workout,
        featured_goal=featured_goal,
        active_goal_count=len(active_goals),
        completed_goal_count=len(completed_goals),
    )


@dashboard_bp.route("/health")
def health():
    return {"status": "ok"}, 200
