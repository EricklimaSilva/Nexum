from __future__ import annotations

from typing import Optional

from app.extensions import db
from app.progression.models import UserProgress, XPEvent

XP_PER_LEVEL_BASE = 100
XP_PER_LEVEL_STEP = 50


def xp_for_next_level(level: int) -> int:
    """Retorna o XP necessário para avançar do nível atual para o próximo."""
    if level < 1:
        raise ValueError("O nível deve ser maior ou igual a 1.")
    return XP_PER_LEVEL_BASE + ((level - 1) * XP_PER_LEVEL_STEP)


def cumulative_xp_before_level(level: int) -> int:
    """Retorna o XP cumulativo necessário antes de um nível específico."""
    if level <= 1:
        return 0
    n = level - 1
    return 25 * n * (n + 3)


def calculate_level(total_xp: int) -> int:
    """Calcula o nível atual de forma eficiente com busca binária."""
    if not isinstance(total_xp, int) or isinstance(total_xp, bool):
        raise TypeError("total_xp deve ser um inteiro.")
    if total_xp < 0:
        raise ValueError("O total de XP não pode ser negativo.")
    if total_xp == 0:
        return 1

    lo = 1
    hi = 2
    while cumulative_xp_before_level(hi + 1) <= total_xp:
        hi *= 2

    while lo < hi:
        mid = (lo + hi) // 2
        if cumulative_xp_before_level(mid + 1) <= total_xp:
            lo = mid + 1
        else:
            hi = mid

    return lo


def calculate_rank(level: int) -> str:
    """Define o rank com base no nível atual."""
    if level < 1:
        raise ValueError("O nível deve ser maior ou igual a 1.")

    if level <= 4:
        return "E"
    if level <= 9:
        return "D"
    if level <= 19:
        return "C"
    if level <= 34:
        return "B"
    if level <= 49:
        return "A"
    return "S"


def get_xp_for_current_level(total_xp: int, level: Optional[int] = None) -> int:
    """Retorna o XP acumulado dentro do nível atual."""
    if total_xp < 0:
        raise ValueError("O total de XP não pode ser negativo.")

    current_level = level if level is not None else calculate_level(total_xp)
    previous_total = cumulative_xp_before_level(current_level)
    return max(0, total_xp - previous_total)


def get_xp_needed_for_next_level(total_xp: int, level: Optional[int] = None) -> int:
    """Retorna o XP necessário para evoluir para o próximo nível."""
    current_level = level if level is not None else calculate_level(total_xp)
    return xp_for_next_level(current_level)


def get_progress_percentage(total_xp: int, level: Optional[int] = None) -> float:
    """Calcula a porcentagem de progresso dentro do nível atual."""
    if total_xp < 0:
        raise ValueError("O total de XP não pode ser negativo.")

    current_level = level if level is not None else calculate_level(total_xp)
    xp_in_current_level = get_xp_for_current_level(total_xp, current_level)
    xp_needed = xp_for_next_level(current_level)
    if xp_needed <= 0:
        return 0.0
    return min(100.0, max(0.0, (xp_in_current_level / xp_needed) * 100.0))


def get_user_progress(user) -> UserProgress:
    """Retorna o progresso do usuário sem criar nem alterar registros."""
    if user is None:
        raise ValueError("Usuário obrigatório.")

    progress = getattr(user, "progress", None)
    if progress is None:
        raise RuntimeError(f"UserProgress não encontrado para o usuário {user.id}.")
    return progress


def sync_progress(progress: UserProgress) -> None:
    """Atualiza level e rank a partir do total_xp do progresso."""
    if progress.total_xp < 0:
        raise ValueError("O total de XP não pode ser negativo.")

    progress.level = calculate_level(progress.total_xp)
    progress.rank = calculate_rank(progress.level)


def ensure_user_progress(user) -> UserProgress:
    """Leitura pura: retorna o progresso existente ou levanta erro explícito."""
    return get_user_progress(user)


def create_initial_progress(user) -> UserProgress:
    """Cria o registro inicial do progresso sem commit e sem duplicar o estado."""
    if user is None:
        raise ValueError("Usuário obrigatório.")
    if getattr(user, "id", None) is None:
        raise ValueError("O usuário precisa estar persistido para receber UserProgress.")

    existing = getattr(user, "progress", None)
    if existing is not None:
        return existing

    progress = UserProgress(user_id=user.id, total_xp=0, level=1, rank="E")
    db.session.add(progress)
    return progress


def award_xp_for_event(user, source_type: str, source_id: int, delta: int, reason: str) -> XPEvent:
    """Concede XP para um evento de origem única e registra um ledger auditável sem commit implícito."""
    if user is None:
        raise ValueError("Usuário obrigatório.")
    if not isinstance(source_type, str) or not source_type.strip():
        raise ValueError("source_type deve ser uma string não vazia.")
    if source_id is None or isinstance(source_id, bool):
        raise ValueError("source_id deve ser informado.")
    if delta is None or isinstance(delta, bool) or not isinstance(delta, int):
        raise ValueError("delta deve ser um inteiro válido.")
    if delta <= 0:
        raise ValueError("delta deve ser positivo.")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason deve ser uma string não vazia.")

    existing = (
        XPEvent.query.filter_by(user_id=user.id, source_type=source_type, source_id=source_id)
        .first()
    )
    if existing is not None:
        return existing

    progress = get_user_progress(user)
    event = XPEvent(
        user_id=user.id,
        source_type=source_type.strip(),
        source_id=int(source_id),
        delta=delta,
        reason=reason.strip(),
    )
    db.session.add(event)
    db.session.flush()

    progress.total_xp += delta
    if progress.total_xp < 0:
        raise ValueError("O total de XP não pode ficar negativo.")

    sync_progress(progress)
    db.session.add(progress)
    return event


def add_xp(user, amount: int, reason: Optional[str] = None) -> UserProgress:
    """Compatibilidade para XP direto sem ledger. Mantém o comportamento atual."""
    if amount is None or isinstance(amount, bool) or not isinstance(amount, int):
        raise ValueError("A quantidade de XP deve ser um inteiro válido.")
    if amount < 0:
        raise ValueError("Não é permitido adicionar XP negativo.")
    if reason is not None and not isinstance(reason, str):
        raise ValueError("O motivo deve ser uma string ou None.")

    progress = get_user_progress(user)
    progress.total_xp += amount
    if progress.total_xp < 0:
        raise ValueError("O total de XP não pode ficar negativo.")

    sync_progress(progress)
    db.session.add(progress)

    return progress
