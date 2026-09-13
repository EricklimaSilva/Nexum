from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.workouts.services import (
    add_workout_exercise,
    add_workout_set,
    create_workout_session,
    get_workout_session_for_user,
    list_workout_sessions_for_user,
)


workouts_bp = Blueprint("workouts", __name__, url_prefix="/workouts")


@workouts_bp.route("/")
@login_required
def index():
    sessions = list_workout_sessions_for_user(current_user)
    selected_session = None

    session_id = request.args.get("session_id", type=int)
    if session_id is not None:
        try:
            selected_session = get_workout_session_for_user(current_user, session_id)
        except RuntimeError:
            flash("Treino não encontrado.", "error")

    return render_template(
        "workouts/index.html",
        sessions=sessions,
        selected_session=selected_session,
    )


@workouts_bp.route("/session", methods=["POST"])
@login_required
def create_session():
    name = request.form.get("name")
    notes = request.form.get("notes")

    try:
        session = create_workout_session(
            current_user,
            name=name,
            notes=notes,
        )
        db.session.commit()
        flash("Treino criado com sucesso.", "success")
        return redirect(url_for("workouts.index", session_id=session.id))
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(url_for("workouts.index"))


@workouts_bp.route("/session/<int:session_id>/exercise", methods=["POST"])
@login_required
def create_exercise(session_id: int):
    name = request.form.get("name")
    category = request.form.get("category") or "other"

    try:
        exercise = add_workout_exercise(
            current_user,
            session_id=session_id,
            name=name,
            category=category,
        )
        db.session.commit()
        flash("Exercício adicionado.", "success")
        return redirect(url_for("workouts.index", session_id=exercise.session_id))
    except (ValueError, TypeError, RuntimeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
        return redirect(url_for("workouts.index", session_id=session_id))


@workouts_bp.route("/exercise/<int:exercise_id>/set", methods=["POST"])
@login_required
def create_set(exercise_id: int):
    reps = request.form.get("reps")
    duration_seconds = request.form.get("duration_seconds")
    session_id = request.form.get("session_id", type=int)

    try:
        workout_set = add_workout_set(
            current_user,
            exercise_id=exercise_id,
            reps=reps,
            duration_seconds=duration_seconds,
      )
        db.session.commit()
        flash("Série registrada.", "success")
        return redirect(
            url_for(
                "workouts.index",
                session_id=workout_set.exercise.session_id,
            )
        )
    except (ValueError, TypeError, RuntimeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
        if session_id is not None:
            return redirect(url_for("workouts.index", session_id=session_id))
        return redirect(url_for("workouts.index"))
