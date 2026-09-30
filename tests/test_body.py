import pytest

from app.body.services import (
    add_body_measurement,
    calculate_bmi,
    get_body_status_for_user,
    get_measurement_history_for_user,
    upsert_body_profile,
)


def test_upsert_body_profile_and_measurement(app, user):
    profile = upsert_body_profile(user, height_cm="175.00")
    measurement = add_body_measurement(user, weight_kg="70.00")

    assert profile.user_id == user.id
    assert profile.height_cm == 175.00
    assert measurement.user_id == user.id
    assert measurement.weight_kg == 70.00


def test_calculate_bmi_returns_expected_value(app):
    bmi = calculate_bmi(height_cm="175.00", weight_kg="70.00")
    assert float(bmi) == pytest.approx(22.86, abs=0.01)


def test_invalid_height_and_weight_are_rejected(app, user):
    with pytest.raises(ValueError):
        upsert_body_profile(user, height_cm="0")

    with pytest.raises(ValueError):
        add_body_measurement(user, weight_kg="0")

    with pytest.raises(ValueError):
        add_body_measurement(user, weight_kg="-10")


def test_measurement_history_is_ordered(app, user):
    add_body_measurement(user, weight_kg="70.00")
    add_body_measurement(user, weight_kg="72.00")

    history = get_measurement_history_for_user(user, limit=10)

    assert len(history) == 2
    assert history[0].weight_kg == 72.00
    assert history[1].weight_kg == 70.00


def test_body_status_and_user_isolation(app, user, second_user):
    upsert_body_profile(user, height_cm="180.00")
    add_body_measurement(user, weight_kg="80.00")

    status = get_body_status_for_user(user)
    assert status["profile"] is not None
    assert status["latest_measurement"] is not None
    assert status["bmi"] is not None

    second_status = get_body_status_for_user(second_user)
    assert second_status["profile"] is None
    assert second_status["latest_measurement"] is None
