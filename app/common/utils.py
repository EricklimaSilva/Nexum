from datetime import UTC
from zoneinfo import ZoneInfo

from flask import flash


SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def safe_flash(message: str, category: str = "info"):
    flash(message, category)


def to_sao_paulo_time(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(SAO_PAULO_TZ)
