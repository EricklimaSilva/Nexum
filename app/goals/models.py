from app.common.utils import utc_now_naive
from app.extensions import db


GOAL_CATEGORIES = (
    "personal",
    "career",
    "study",
    "finance",
    "health",
    "relationship",
    "other",
)

GOAL_STATUSES = ("active", "completed")


class Goal(db.Model):
    __tablename__ = "goals"
    __table_args__ = (
        db.CheckConstraint(
            "category IN ('personal', 'career', 'study', 'finance', 'health', 'relationship', 'other')",
            name="ck_goal_category",
        ),
        db.CheckConstraint(
            "status IN ('active', 'completed')",
            name="ck_goal_status",
        ),
        db.CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_goal_progress_percent",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(30), nullable=False, default="personal")
    progress_percent = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="active")
    target_date = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now_naive)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now_naive,
        onupdate=utc_now_naive,
    )

    user = db.relationship("User", back_populates="goals")
