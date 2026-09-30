import re
import unicodedata
from datetime import timedelta

from app.common.utils import utc_now_naive
from app.extensions import db
from app.progression.services import award_xp_for_event
from app.quick_log.models import QuickLog

VALID_QUICK_LOG_CATEGORIES = {
    "personal",
    "career",
    "study",
    "finance",
    "health",
    "relationship",
    "other",
}


def _normalize_action_for_dedupe(value: str) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _clean_action(value) -> str:
    if value is None:
        raise ValueError("Ação é obrigatória.")

    action = str(value).strip()

    if not action:
        raise ValueError("Ação é obrigatória.")

    if len(action) > 160:
        raise ValueError("Ação deve ter no máximo 160 caracteres.")

    return action


def _clean_category(value):
    if value is None:
        return None

    category = str(value).strip().lower()

    if not category:
        return None

    if len(category) > 40:
        raise ValueError("Categoria deve ter no máximo 40 caracteres.")

    if category not in VALID_QUICK_LOG_CATEGORIES:
        raise ValueError("Categoria inválida. Use: personal, career, study, finance, health, relationship ou other.")

    return category


def _parse_xp(value) -> int:
    if value is None:
        return 0

    if isinstance(value, bool):
        raise ValueError("XP inválido.")

    try:
        xp = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("XP deve ser um número inteiro.") from exc

    if xp < 0:
        raise ValueError("XP não pode ser negativo.")

    return xp


def list_quick_logs_for_user(user, limit: int = 20):
    if limit < 1:
        raise ValueError("Limite deve ser maior que zero.")

    return (
        QuickLog.query
        .filter_by(user_id=user.id)
        .order_by(QuickLog.created_at.desc(), QuickLog.id.desc())
        .limit(limit)
        .all()
    )


def create_quick_log(
    user,
    *,
    action,
    category=None,
    xp_awarded=0,
) -> QuickLog:
    clean_action = _clean_action(action)
    clean_category = _clean_category(category)
    clean_xp = _parse_xp(xp_awarded)
    normalized_action = _normalize_action_for_dedupe(clean_action)

    recent_logs = (
        QuickLog.query.filter_by(user_id=user.id)
        .filter(QuickLog.created_at >= utc_now_naive() - timedelta(minutes=10))
        .all()
    )
    for recent in recent_logs:
        if _normalize_action_for_dedupe(recent.action) == normalized_action:
            raise ValueError("A mesma ação foi registrada recentemente. Espere 10 minutos antes de repetir.")

    quick_log = QuickLog(
        user_id=user.id,
        action=clean_action,
        category=clean_category,
        xp_awarded=clean_xp,
    )

    db.session.add(quick_log)
    db.session.flush()

    if clean_xp > 0:
        award_xp_for_event(
            user,
            "quick_log",
            quick_log.id,
            clean_xp,
            f"quick_log:{clean_action}",
        )

    return quick_log
