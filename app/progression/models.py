from app.common.utils import utc_now_naive
from app.extensions import db


class UserProgress(db.Model):
    __tablename__ = "user_progress"
    __table_args__ = (
        db.CheckConstraint("total_xp >= 0", name="ck_user_progress_total_xp_non_negative"),
        db.CheckConstraint("level >= 1", name="ck_user_progress_level_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    total_xp = db.Column(db.BigInteger, default=0, nullable=False)
    level = db.Column(db.Integer, default=1, nullable=False)
    rank = db.Column(db.String(10), default="E", nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now_naive, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now_naive, onupdate=utc_now_naive, nullable=False)

    user = db.relationship("User", backref=db.backref("progress", uselist=False, cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<UserProgress user_id={self.user_id} level={self.level} rank={self.rank}>"


class XPEvent(db.Model):
    __tablename__ = "xp_events"
    __table_args__ = (
        db.UniqueConstraint("user_id", "source_type", "source_id", name="uq_xp_event_user_source"),
        db.CheckConstraint("delta > 0", name="ck_xp_event_delta_positive"),
        db.Index("ix_xp_event_user_created_at", "user_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=False)
    source_id = db.Column(db.Integer, nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now_naive, nullable=False)

    user = db.relationship("User", backref=db.backref("xp_events", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<XPEvent user_id={self.user_id} source_type={self.source_type} delta={self.delta}>"
