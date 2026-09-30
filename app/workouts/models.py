from sqlalchemy import CheckConstraint, UniqueConstraint

from app.common.utils import utc_now_naive
from app.extensions import db


class WorkoutSession(db.Model):
    __tablename__ = "workout_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    performed_at = db.Column(db.DateTime, default=utc_now_naive, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now_naive, nullable=False)

    user = db.relationship(
        "User",
        backref=db.backref(
            "workout_sessions",
            cascade="all, delete-orphan",
        ),
    )

    def __repr__(self) -> str:
        return f"<WorkoutSession user_id={self.user_id} name={self.name!r}>"


class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        CheckConstraint(
            "category IN ('pull', 'push', 'core', 'legs', 'skill', 'mobility', 'other')",
            name="ck_workout_exercise_category",
        ),
        CheckConstraint(
            "order_index >= 0",
            name="ck_workout_exercise_order_nonnegative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("workout_sessions.id"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(20), nullable=False, default="other")
    order_index = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=utc_now_naive, nullable=False)

    session = db.relationship(
        "WorkoutSession",
        backref=db.backref(
            "exercises",
            cascade="all, delete-orphan",
            order_by="WorkoutExercise.order_index",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkoutExercise session_id={self.session_id} "
            f"name={self.name!r} category={self.category}>"
        )


class WorkoutSet(db.Model):
    __tablename__ = "workout_sets"
    __table_args__ = (
        CheckConstraint(
            "set_number > 0",
            name="ck_workout_set_number_positive",
        ),
        CheckConstraint(
            "reps IS NULL OR reps > 0",
            name="ck_workout_set_reps_positive",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_workout_set_duration_positive",
        ),
        CheckConstraint(
            "reps IS NOT NULL OR duration_seconds IS NOT NULL",
            name="ck_workout_set_has_metric",
        ),
        UniqueConstraint(
            "exercise_id",
            "set_number",
            name="uq_workout_set_exercise_number",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(
        db.Integer,
        db.ForeignKey("workout_exercises.id"),
        nullable=False,
        index=True,
    )
    set_number = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now_naive, nullable=False)

    exercise = db.relationship(
        "WorkoutExercise",
        backref=db.backref(
            "sets",
            cascade="all, delete-orphan",
            order_by="WorkoutSet.set_number",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkoutSet exercise_id={self.exercise_id} "
            f"set_number={self.set_number}>"
        )
