from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.common.utils import safe_flash
from app.extensions import db
from app.goals import goals_bp
from app.goals.models import GOAL_CATEGORIES
from app.goals.services import (
    complete_goal,
    create_goal,
    list_goals_for_user,
    update_goal_progress,
)


@goals_bp.route("/")
@login_required
def index():
    goals = list_goals_for_user(current_user)
    active_goals = [goal for goal in goals if goal.status == "active"]
    completed_goals = [goal for goal in goals if goal.status == "completed"]

    return render_template(
        "goals/index.html",
        goals=goals,
        active_goals=active_goals,
        completed_goals=completed_goals,
        categories=GOAL_CATEGORIES,
    )


@goals_bp.route("/", methods=["POST"])
@login_required
def create():
    try:
        goal = create_goal(
            current_user,
            title=request.form.get("title"),
            description=request.form.get("description"),
            category=request.form.get("category"),
            target_date=request.form.get("target_date"),
        )
        db.session.commit()
        safe_flash(f"Meta '{goal.title}' criada com sucesso.", "success")
    except (TypeError, ValueError) as exc:
        db.session.rollback()
        safe_flash(str(exc), "error")
    except Exception:
        db.session.rollback()
        raise

    return redirect(url_for("goals.index"))


@goals_bp.route("/<int:goal_id>/progress", methods=["POST"])
@login_required
def update_progress(goal_id: int):
    try:
        goal = update_goal_progress(
            current_user,
            goal_id=goal_id,
            progress_percent=request.form.get("progress_percent"),
        )
        db.session.commit()
        safe_flash(
            f"Progresso de '{goal.title}' atualizado para {goal.progress_percent}%.",
            "success",
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        db.session.rollback()
        safe_flash(str(exc), "error")
    except Exception:
        db.session.rollback()
        raise

    return redirect(url_for("goals.index"))


@goals_bp.route("/<int:goal_id>/complete", methods=["POST"])
@login_required
def complete(goal_id: int):
    try:
        goal = complete_goal(current_user, goal_id=goal_id)
        db.session.commit()
        safe_flash(f"Meta '{goal.title}' concluída.", "success")
    except (TypeError, ValueError, RuntimeError) as exc:
        db.session.rollback()
        safe_flash(str(exc), "error")
    except Exception:
        db.session.rollback()
        raise

    return redirect(url_for("goals.index"))
