import re


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def sanitize_text(value: str | None, default: str = "") -> str:
    if value is None:
        return default
    return value.strip()
