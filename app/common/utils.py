from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from flask import flash


SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def utc_now_naive() -> datetime:
    """Retorna o timestamp atual em UTC sem timezone, compatível com colunas existentes do schema."""
    return datetime.now(UTC).replace(tzinfo=None)


def safe_flash(message: str, category: str = "info"):
    flash(message, category)


def to_sao_paulo_time(value):
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(SAO_PAULO_TZ)
