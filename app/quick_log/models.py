from datetime import datetime

from app.extensions import db


class QuickLog(db.Model):
    __tablename__ = "quick_logs"
    __table_args__ = (
        db.CheckConstraint(
            "xp_awarded >= 0",
            name="ck_quick_log_xp_awarded_non_negative",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    action = db.Column(
        db.String(160),
        nullable=False,
    )

    category = db.Column(
        db.String(40),
        nullable=True,
    )

    xp_awarded = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user = db.relationship(
        "User",
        back_populates="quick_logs",
    )

    def __repr__(self) -> str:
        return f"<QuickLog id={self.id} user_id={self.user_id} action={self.action!r}>"
