from flask import Blueprint, render_template
from flask_login import current_user, login_required

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

    return render_template(
        "dashboard/index.html",
        progress=progress,
        xp_current=xp_current,
        xp_next=xp_next,
        progress_percent=progress_percent,
        user_name=current_user.profile.name,
    )


@dashboard_bp.route("/health")
def health():
    return {"status": "ok"}, 200
