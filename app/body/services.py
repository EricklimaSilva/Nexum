from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.body.models import BodyMeasurement, BodyProfile
from app.extensions import db


TWO_PLACES = Decimal("0.01")


def parse_decimal(value, field_name: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field_name} is required.")

    if isinstance(value, Decimal):
        parsed = value
    elif isinstance(value, (int, float)):
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        normalized = value.strip().replace(",", ".")
        if not normalized:
            raise ValueError(f"{field_name} is required.")
        try:
            parsed = Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be numeric.") from exc
    else:
        raise ValueError(f"{field_name} must be numeric.")

    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite.")

    return parsed.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def get_body_profile_for_user(user):
    return BodyProfile.query.filter_by(user_id=user.id).first()


def get_latest_measurement_for_user(user):
    return (
        BodyMeasurement.query.filter_by(user_id=user.id)
        .order_by(
            BodyMeasurement.measured_at.desc(),
            BodyMeasurement.id.desc(),
        )
        .first()
    )


def get_measurement_history_for_user(user, limit: int = 20):
    return (
        BodyMeasurement.query.filter_by(user_id=user.id)
        .order_by(
            BodyMeasurement.measured_at.desc(),
            BodyMeasurement.id.desc(),
        )
        .limit(limit)
        .all()
    )


def upsert_body_profile(user, *, height_cm):
    parsed_height = parse_decimal(height_cm, "height_cm")

    if parsed_height <= 0 or parsed_height > Decimal("300.00"):
        raise ValueError("height_cm must be between 0 and 300.")

    profile = get_body_profile_for_user(user)

    if profile is None:
        profile = BodyProfile(
            user_id=user.id,
            height_cm=parsed_height,
        )
        db.session.add(profile)
    else:
        profile.height_cm = parsed_height

    return profile


def add_body_measurement(user, *, weight_kg, measured_at=None):
    parsed_weight = parse_decimal(weight_kg, "weight_kg")

    if parsed_weight <= 0 or parsed_weight > Decimal("500.00"):
        raise ValueError("weight_kg must be between 0 and 500.")

    measurement = BodyMeasurement(
        user_id=user.id,
        weight_kg=parsed_weight,
    )

    if measured_at is not None:
        measurement.measured_at = measured_at

    db.session.add(measurement)
    return measurement


def calculate_bmi(*, height_cm, weight_kg):
    parsed_height = parse_decimal(height_cm, "height_cm")
    parsed_weight = parse_decimal(weight_kg, "weight_kg")

    if parsed_height <= 0 or parsed_weight <= 0:
        raise ValueError("height_cm and weight_kg must be greater than zero.")

    height_m = parsed_height / Decimal("100")
    bmi = parsed_weight / (height_m * height_m)

    return bmi.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def get_body_status_for_user(user):
    profile = get_body_profile_for_user(user)
    latest = get_latest_measurement_for_user(user)

    bmi = None
    if profile is not None and latest is not None:
        bmi = calculate_bmi(
            height_cm=profile.height_cm,
            weight_kg=latest.weight_kg,
        )

    return {
        "profile": profile,
        "latest_measurement": latest,
        "bmi": bmi,
    }
