from decimal import Decimal

import pytest

from app.extensions import db
from app.finance.services import (
    calculate_safe_spend,
    create_commitment,
    delete_commitment,
    get_commitment_for_user,
    mark_commitment_paid,
    update_finance_settings,
)


def test_finance_settings_are_created_and_updated(app, user):
    settings = user.finance_settings
    assert settings is not None

    updated = update_finance_settings(
        user,
        current_balance="2500.00",
        protected_savings="300.00",
        payday_first=10,
        payday_second=20,
    )

    assert updated.current_balance == Decimal("2500.00")
    assert updated.protected_savings == Decimal("300.00")
    assert updated.payday_first == 10
    assert updated.payday_second == 20


def test_calculate_safe_spend_returns_expected_summary(app, user):
    update_finance_settings(
        user,
        current_balance="1500.00",
        protected_savings="200.00",
        payday_first=10,
        payday_second=20,
    )

    summary = calculate_safe_spend(user, reference_date=None)

    assert summary["settings"].user_id == user.id
    assert summary["pending_total"] >= Decimal("0.00")
    assert summary["available_to_spend"] >= Decimal("0.00")


def test_commitment_creation_and_toggle(app, user):
    commitment = create_commitment(
        user,
        name="Internet",
        amount="120.50",
        due_date="2026-12-15",
        kind="fixed",
        is_paid=False,
    )

    assert commitment.user_id == user.id
    assert commitment.amount == Decimal("120.50")
    assert commitment.is_paid is False

    toggled = mark_commitment_paid(commitment, is_paid=True)
    assert toggled.is_paid is True


def test_delete_commitment_and_user_isolation(app, user, second_user):
    commitment = create_commitment(
        user,
        name="Aluguel",
        amount="500.00",
        due_date="2026-12-20",
        kind="fixed",
        is_paid=False,
    )
    db.session.flush()

    delete_commitment(commitment)

    with pytest.raises(RuntimeError):
        get_commitment_for_user(second_user, commitment.id)


def test_commitment_access_is_isolated_between_users(app, user, second_user):
    commitment = create_commitment(
        user,
        name="Cartão",
        amount="200.00",
        due_date="2026-12-15",
        kind="variable",
        is_paid=False,
    )

    with pytest.raises(RuntimeError):
        get_commitment_for_user(second_user, commitment.id)
