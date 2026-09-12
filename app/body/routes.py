from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.body.services import (
    add_body_measurement,
    get_body_status_for_user,
    get_measurement_history_for_user,
    upsert_body_profile,
)
from app.extensions import db


body_bp = Blueprint("body", __name__, url_prefix="/body")


@body_bp.route("/")
@login_required
def index():
    status = get_body_status_for_user(current_user)
    history = get_measurement_history_for_user(current_user)

    return render_template(
        "body/index.html",
        status=status,
        history=history,
    )


@body_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    height_cm = request.form.get("height_cm")

    try:
        upsert_body_profile(
            current_user,
            height_cm=height_cm,
        )
        db.session.commit()
        flash("Dados corporais atualizados.", "success")
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")

    return redirect(url_for("body.index"))


@body_bp.route("/measurement", methods=["POST"])
@login_required
def create_measurement():
    weight_kg = request.form.get("weight_kg")

    try:
        add_body_measurement(
            current_user,
            weight_kg=weight_kg,
        )
        db.session.commit()
        flash("Peso registrado com sucesso.", "success")
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")

    return redirect(url_for("body.index"))
