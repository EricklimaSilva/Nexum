from app.extensions import db
from app.workouts.models import WorkoutExercise, WorkoutSession, WorkoutSet


EXERCISE_CATEGORIES = {
    "pull",
    "push",
    "core",
    "legs",
    "skill",
    "mobility",
    "other",
}


def clean_required_text(value, field_name: str, max_length: int) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required.")

    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    if len(cleaned) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters.")
    return cleaned


def clean_optional_text(value, max_length: int = 2000):
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError(f"text must be at most {max_length} characters.")
    return cleaned


def parse_positive_int(value, field_name: str, *, required: bool = True):
    if value is None or value == "":
        if required:
            raise ValueError(f"{field_name} is required.")
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return parsed


def get_workout_session_for_user(user, session_id: int):
    session = WorkoutSession.query.filter_by(
        id=session_id,
        user_id=user.id,
    ).first()
    if session is None:
        raise RuntimeError("workout session not found.")
    return session


def get_workout_exercise_for_user(user, exercise_id: int):
    exercise = (
        WorkoutExercise.query
        .join(WorkoutSession, WorkoutExercise.session_id == WorkoutSession.id)
        .filter(
            WorkoutExercise.id == exercise_id,
            WorkoutSession.user_id == user.id,
        )
        .first()
    )
    if exercise is None:
        raise RuntimeError("workout exercise not found.")
    return exercise


def list_workout_sessions_for_user(user, limit: int = 20):
    return (
        WorkoutSession.query.filter_by(user_id=user.id)
        .order_by(WorkoutSession.performed_at.desc(), WorkoutSession.id.desc())
        .limit(limit)
        .all()
    )


def create_workout_session(user, *, name, notes=None, performed_at=None):
    clean_name = clean_required_text(name, "name", 120)
    clean_notes = clean_optional_text(notes)

    session = WorkoutSession(
        user_id=user.id,
        name=clean_name,
        notes=clean_notes,
    )
    if performed_at is not None:
        session.performed_at = performed_at

    db.session.add(session)
    return session


def add_workout_exercise(user, *, session_id, name, category="other"):
    session = get_workout_session_for_user(user, session_id)
    clean_name = clean_required_text(name, "name", 120)
    clean_category = (str(category or "other").strip().lower())

    if clean_category not in EXERCISE_CATEGORIES:
        raise ValueError("invalid exercise category.")

    next_order = len(session.exercises)
    exercise = WorkoutExercise(
        session_id=session.id,
        name=clean_name,
        category=clean_category,
        order_index=next_order,
    )
    db.session.add(exercise)
    return exercise


def add_workout_set(user, *, exercise_id, reps=None, duration_seconds=None):
    exercise = get_workout_exercise_for_user(user, exercise_id)

    parsed_reps = parse_positive_int(reps, "reps", required=False)
    parsed_duration = parse_positive_int(
        duration_seconds,
        "duration_seconds",
        required=False,
    )

    if parsed_reps is None and parsed_duration is None:
        raise ValueError("reps or duration_seconds is required.")

    next_set_number = len(exercise.sets) + 1
    workout_set = WorkoutSet(
        exercise_id=exercise.id,
        set_number=next_set_number,
        reps=parsed_reps,
        duration_seconds=parsed_duration,
    )
    db.session.add(workout_set)
    return workout_set
