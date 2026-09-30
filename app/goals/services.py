from datetime import date

from app.common.utils import utc_now_naive
from app.extensions import db
from app.goals.models import GOAL_CATEGORIES, GOAL_STATUSES, Goal


def _clean_required_text(value, field_name: str, max_length: int) -> str:
    if value is None:
        raise ValueError(f"{field_name} é obrigatório.")

    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{field_name} é obrigatório.")
    if len(cleaned) > max_length:
        raise ValueError(
            f"{field_name} deve ter no máximo {max_length} caracteres."
        )

    return cleaned


def _clean_optional_text(value):
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned or None


def _parse_target_date(value):
    if value is None or value == "":
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    try:
        return date.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Prazo inválido.") from exc


def _parse_progress_percent(value) -> int:
    if isinstance(value, bool):
        raise TypeError("Progresso inválido.")

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Progresso deve ser um número inteiro.") from exc

    if parsed < 0 or parsed > 99:
        raise ValueError(
            "Progresso deve estar entre 0 e 99. "
            "Para concluir a meta, use a ação de conclusão."
        )

    return parsed


def get_goal_for_user(user, goal_id: int) -> Goal:
    goal = Goal.query.filter_by(id=goal_id, user_id=user.id).first()
    if goal is None:
        raise RuntimeError("Meta não encontrada.")

    return goal


def list_goals_for_user(user, status: str | None = None):
    query = Goal.query.filter_by(user_id=user.id)

    if status is not None:
        if status not in GOAL_STATUSES:
            raise ValueError("Status de meta inválido.")
        query = query.filter_by(status=status)

    return query.order_by(Goal.created_at.desc(), Goal.id.desc()).all()


def create_goal(
    user,
    *,
    title,
    description=None,
    category="personal",
    target_date=None,
) -> Goal:
    clean_title = _clean_required_text(title, "Título", 160)
    clean_description = _clean_optional_text(description)
    clean_category = str(category or "personal").strip().lower()

    if clean_category not in GOAL_CATEGORIES:
        raise ValueError("Categoria de meta inválida.")

    goal = Goal(
        user_id=user.id,
        title=clean_title,
        description=clean_description,
        category=clean_category,
        target_date=_parse_target_date(target_date),
        progress_percent=0,
        status="active",
    )
    db.session.add(goal)
    return goal


def update_goal_progress(
    user,
    *,
    goal_id: int,
    progress_percent,
) -> Goal:
    goal = get_goal_for_user(user, goal_id)

    if goal.status != "active":
        raise ValueError("Meta concluída não pode ter o progresso alterado.")

    goal.progress_percent = _parse_progress_percent(progress_percent)
    return goal


def complete_goal(user, *, goal_id: int) -> Goal:
    goal = get_goal_for_user(user, goal_id)

    if goal.status != "active":
        raise ValueError("Meta já concluída.")

    goal.progress_percent = 100
    goal.status = "completed"
    goal.completed_at = utc_now_naive()
    return goal
