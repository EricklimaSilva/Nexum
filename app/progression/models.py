from datetime import datetime

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("progress", uselist=False, cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<UserProgress user_id={self.user_id} level={self.level} rank={self.rank}>"
