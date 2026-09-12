from datetime import datetime

from sqlalchemy import CheckConstraint

from app.extensions import db


class BodyProfile(db.Model):
    __tablename__ = "body_profiles"
    __table_args__ = (
        CheckConstraint("height_cm > 0", name="ck_body_profile_height_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    height_cm = db.Column(db.Numeric(5, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "body_profile",
            uselist=False,
            cascade="all, delete-orphan",
        ),
    )

    def __repr__(self) -> str:
        return f"<BodyProfile user_id={self.user_id} height_cm={self.height_cm}>"


class BodyMeasurement(db.Model):
    __tablename__ = "body_measurements"
    __table_args__ = (
        CheckConstraint("weight_kg > 0", name="ck_body_measurement_weight_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    weight_kg = db.Column(db.Numeric(6, 2), nullable=False)
    measured_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship(
        "User",
        backref=db.backref(
            "body_measurements",
            cascade="all, delete-orphan",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<BodyMeasurement user_id={self.user_id} "
            f"weight_kg={self.weight_kg}>"
        )
