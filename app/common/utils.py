from flask import flash


def safe_flash(message: str, category: str = "info"):
    flash(message, category)
