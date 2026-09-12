from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.finance.models import FinanceCommitment
from app.finance.services import (
    calculate_safe_spend,
    create_commitment,
    delete_commitment,
    get_commitment_for_user,
    get_finance_settings_for_user,
    mark_commitment_paid,
    update_finance_settings,
)

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")


@finance_bp.route("/")
@login_required
def index():
    try:
        settings = get_finance_settings_for_user(current_user)
        safe_spend = calculate_safe_spend(current_user)
    except RuntimeError as exc:
        flash(str(exc), "error")
        return render_template(
            "finance/index.html",
            settings=None,
            safe_spend=None,
            commitments=[],
            error=str(exc),
        )

    commitments = FinanceCommitment.query.filter_by(user_id=current_user.id).order_by(FinanceCommitment.due_date.asc()).all()

    return render_template(
        "finance/index.html",
        settings=settings,
        safe_spend=safe_spend,
        commitments=commitments,
        error=None,
    )


@finance_bp.route("/settings", methods=["POST"])
@login_required
def update_settings():
    current_balance = request.form.get("current_balance")
    protected_savings = request.form.get("protected_savings")
    payday_first = request.form.get("payday_first")
    payday_second = request.form.get("payday_second")

    try:
        update_finance_settings(
            current_user,
            current_balance=current_balance,
            protected_savings=protected_savings,
            payday_first=payday_first,
            payday_second=payday_second,
        )
        db.session.commit()
        flash("Configurações financeiras atualizadas.", "success")
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")

    return redirect(url_for("finance.index"))


@finance_bp.route("/commitment", methods=["POST"])
@login_required
def create_finance_commitment():
    name = (request.form.get("name") or "").strip()
    amount = request.form.get("amount")
    due_date = request.form.get("due_date")
    kind = (request.form.get("kind") or "fixed").strip()

    try:
        commitment = create_commitment(
            current_user,
            name=name,
            amount=amount,
            due_date=due_date,
            kind=kind,
            is_paid=False,
        )
        db.session.commit()
        flash("Compromisso cadastrado com sucesso.", "success")
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")

    return redirect(url_for("finance.index"))


@finance_bp.route("/commitment/<int:commitment_id>/toggle-paid", methods=["POST"])
@login_required
def toggle_commitment_paid(commitment_id: int):
    try:
        commitment = get_commitment_for_user(current_user, commitment_id)
    except RuntimeError:
        flash("Compromisso não encontrado.", "error")
        return redirect(url_for("finance.index"))

    try:
        mark_commitment_paid(commitment, is_paid=not commitment.is_paid)
        db.session.commit()
        flash("Status do compromisso atualizado.", "success")
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")

    return redirect(url_for("finance.index"))


@finance_bp.route("/commitment/<int:commitment_id>/delete", methods=["POST"])
@login_required
def delete_finance_commitment(commitment_id: int):
    try:
        commitment = get_commitment_for_user(current_user, commitment_id)
    except RuntimeError:
        flash("Compromisso não encontrado.", "error")
        return redirect(url_for("finance.index"))

    try:
        delete_commitment(commitment)
        db.session.commit()
        flash("Compromisso removido.", "success")
    except (ValueError, TypeError) as exc:
        db.session.rollback()
        flash(str(exc), "error")

    return redirect(url_for("finance.index"))
