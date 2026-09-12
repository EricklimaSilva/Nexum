from datetime import datetime

from sqlalchemy import CheckConstraint

from app.extensions import db


class FinanceSettings(db.Model):
    __tablename__ = "finance_settings"
    __table_args__ = (
        CheckConstraint("protected_savings >= 0", name="ck_finance_settings_protected_savings_non_negative"),
        CheckConstraint("payday_first BETWEEN 1 AND 31", name="ck_finance_settings_payday_first_valid"),
        CheckConstraint("payday_second BETWEEN 1 AND 31", name="ck_finance_settings_payday_second_valid"),
        CheckConstraint("payday_first <> payday_second", name="ck_finance_settings_paydays_different"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    current_balance = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    protected_savings = db.Column(db.Numeric(14, 2), default=0, nullable=False)
    payday_first = db.Column(db.Integer, default=15, nullable=False)
    payday_second = db.Column(db.Integer, default=30, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("finance_settings", uselist=False, cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<FinanceSettings user_id={self.user_id}>"


class FinanceCommitment(db.Model):
    __tablename__ = "finance_commitments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_finance_commitment_amount_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(160), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    kind = db.Column(db.String(30), nullable=False)
    is_paid = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("finance_commitments", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<FinanceCommitment {self.name} user_id={self.user_id}>"
