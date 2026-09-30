from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.common.utils import safe_flash
from app.extensions import db, limiter
from app.quick_log import quick_log_bp
from app.quick_log.services import create_quick_log, list_quick_logs_for_user


QUICK_LOG_XP = 10


@quick_log_bp.route("/")
@login_required
def index():
    logs = list_quick_logs_for_user(current_user)

    return render_template(
        "quick_log/index.html",
        logs=logs,
        quick_log_xp=QUICK_LOG_XP,
    )


@quick_log_bp.route("/", methods=["POST"])
@login_required
@limiter.limit("20 per minute", key_func=lambda: str(current_user.id))
def create():
    try:
        quick_log = create_quick_log(
            current_user,
            action=request.form.get("action"),
            category=request.form.get("category"),
            xp_awarded=QUICK_LOG_XP,
        )

        db.session.commit()

        safe_flash(
            f"'{quick_log.action}' registrado. +{quick_log.xp_awarded} XP.",
            "success",
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        db.session.rollback()
        safe_flash(str(exc), "error")
    except Exception:
        db.session.rollback()
        raise

    return redirect(url_for("quick_log.index"))
