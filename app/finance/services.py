from __future__ import annotations

import calendar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Optional

from app.extensions import db
from app.finance.models import FinanceCommitment, FinanceSettings

MONEY_QUANT = Decimal("0.01")


def parse_money(value: object, *, field_name: str = "valor") -> Decimal:
    """Converte texto ou número em Decimal monetário válido sem usar float."""
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field_name} é obrigatório.")

    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, str):
        normalized = value.strip().replace(" ", "")
        if not normalized or normalized.lower() in {"nan", "inf", "infinity", "-inf", "-infinity", "+inf", "+infinity"}:
            raise ValueError(f"{field_name} inválido.")

        if "," in normalized and "." in normalized:
            decimal_sep = "," if normalized.rfind(",") > normalized.rfind(".") else "."
            thousand_sep = "." if decimal_sep == "," else ","
            normalized = normalized.replace(thousand_sep, "").replace(decimal_sep, ".")
        elif "," in normalized:
            if normalized.count(",") > 1:
                integer_part, fractional_part = normalized.rsplit(",", 1)
                normalized = integer_part.replace(",", "") + "." + fractional_part
            else:
                normalized = normalized.replace(",", ".")
        elif "." in normalized:
            if normalized.count(".") > 1:
                integer_part, fractional_part = normalized.rsplit(".", 1)
                normalized = integer_part.replace(".", "") + "." + fractional_part

        try:
            decimal_value = Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} inválido.") from exc
    else:
        raise ValueError(f"{field_name} inválido.")

    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} inválido.")

    return decimal_value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def normalize_money(value: Decimal) -> Decimal:
    """Arredonda valores monetários para 2 casas decimais."""
    if value is None:
        raise ValueError("Valor monetário obrigatório.")
    if not isinstance(value, Decimal):
        raise TypeError("Valor monetário deve ser Decimal.")
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def get_finance_settings_for_user(user) -> FinanceSettings:
    """Retorna as configurações financeiras do usuário sem criar registro."""
    if user is None:
        raise ValueError("Usuário obrigatório.")

    settings = getattr(user, "finance_settings", None)
    if settings is None:
        raise RuntimeError(f"FinanceSettings não encontrado para o usuário {user.id}.")
    return settings


def create_initial_finance_settings(user) -> FinanceSettings:
    """Cria as configurações financeiras iniciais de um usuário novo."""
    if user is None:
        raise ValueError("Usuário obrigatório.")
    if getattr(user, "id", None) is None:
        raise ValueError("O usuário precisa estar persistido para receber FinanceSettings.")

    existing = getattr(user, "finance_settings", None)
    if existing is not None:
        return existing

    settings = FinanceSettings(
        user_id=user.id,
        current_balance=Decimal("0.00"),
        protected_savings=Decimal("0.00"),
        payday_first=15,
        payday_second=30,
    )
    db.session.add(settings)
    return settings


def get_valid_payday_day(month_year: tuple[int, int], payday: int) -> int:
    """Retorna o último dia válido do mês para um payday configurado."""
    year, month = month_year
    last_day = calendar.monthrange(year, month)[1]
    return min(payday, last_day)


def get_next_payday(settings: FinanceSettings, reference_date: Optional[date] = None) -> date:
    """Retorna o próximo payday real e estritamente futuro para a data de referência."""
    if settings is None:
        raise ValueError("FinanceSettings obrigatório.")

    today = reference_date or date.today()
    year = today.year
    month = today.month

    for _ in range(2):
        candidates = set()
        for payday in (settings.payday_first, settings.payday_second):
            valid_day = get_valid_payday_day((year, month), payday)
            candidates.add(date(year, month, valid_day))

        future_candidates = sorted(candidate for candidate in candidates if candidate > today)
        if future_candidates:
            return future_candidates[0]

        month += 1
        if month == 13:
            month = 1
            year += 1

    raise ValueError("Não foi possível determinar um próximo payday válido.")


def get_days_until_payday(settings: FinanceSettings, reference_date: Optional[date] = None) -> int:
    """Número de dias restantes até o próximo payday, sem incluir o próprio dia do pagamento."""
    today = reference_date or date.today()
    next_payday = get_next_payday(settings, today)
    delta = (next_payday - today).days
    return max(0, delta)


def get_pending_commitments(user, payday_date: date, reference_date: Optional[date] = None) -> list[FinanceCommitment]:
    """Compromissos pendentes entre hoje e o próximo payday."""
    if user is None:
        raise ValueError("Usuário obrigatório.")

    today = reference_date or date.today()
    return (
        FinanceCommitment.query.filter_by(user_id=user.id, is_paid=False)
        .filter(FinanceCommitment.due_date >= today)
        .filter(FinanceCommitment.due_date <= payday_date)
        .order_by(FinanceCommitment.due_date.asc(), FinanceCommitment.created_at.asc())
        .all()
    )


def get_total_pending_commitments(user, payday_date: date, reference_date: Optional[date] = None) -> Decimal:
    """Soma total dos compromissos pendentes até o payday."""
    commitments = get_pending_commitments(user, payday_date, reference_date)
    return sum((parse_money(item.amount, field_name=item.name) for item in commitments), Decimal("0.00"))


def calculate_safe_spend(user, reference_date: Optional[date] = None) -> dict:
    """Calcula Safe Spend do usuário para o próximo pagamento."""
    if user is None:
        raise ValueError("Usuário obrigatório.")

    settings = get_finance_settings_for_user(user)
    today = reference_date or date.today()
    next_payday = get_next_payday(settings, today)
    remaining_days = get_days_until_payday(settings, today)
    pending_commitments = get_pending_commitments(user, next_payday, today)
    pending_total = sum((parse_money(item.amount, field_name=item.name) for item in pending_commitments), Decimal("0.00"))

    available_to_spend = (
        parse_money(settings.current_balance, field_name="current_balance")
        - pending_total
        - parse_money(settings.protected_savings, field_name="protected_savings")
    )
    if available_to_spend < 0:
        available_to_spend = Decimal("0.00")

    if remaining_days <= 0:
        daily_safe_spend = Decimal("0.00")
    else:
        daily_safe_spend = (available_to_spend / Decimal(remaining_days)).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)

    return {
        "settings": settings,
        "today": today,
        "next_payday": next_payday,
        "remaining_days": remaining_days,
        "pending_commitments": pending_commitments,
        "pending_total": pending_total.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP),
        "protected_savings": parse_money(settings.protected_savings, field_name="protected_savings").quantize(MONEY_QUANT, rounding=ROUND_HALF_UP),
        "available_to_spend": available_to_spend.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP),
        "daily_safe_spend": daily_safe_spend,
    }


def update_finance_settings(user, *, current_balance=None, protected_savings=None, payday_first=None, payday_second=None) -> FinanceSettings:
    """Atualiza as configurações financeiras do usuário após validação completa."""
    settings = get_finance_settings_for_user(user)

    validated_balance = settings.current_balance if current_balance is None else parse_money(current_balance, field_name="saldo atual")
    validated_protected = settings.protected_savings if protected_savings is None else parse_money(protected_savings, field_name="valor protegido")

    if validated_protected < Decimal("0.00"):
        raise ValueError("O valor protegido não pode ser negativo.")

    validated_first = settings.payday_first if payday_first is None else int(payday_first)
    validated_second = settings.payday_second if payday_second is None else int(payday_second)

    if validated_first < 1 or validated_first > 31:
        raise ValueError("payday_first deve estar entre 1 e 31.")
    if validated_second < 1 or validated_second > 31:
        raise ValueError("payday_second deve estar entre 1 e 31.")
    if validated_first == validated_second:
        raise ValueError("Os dois paydays não podem ser iguais.")

    settings.current_balance = validated_balance
    settings.protected_savings = validated_protected
    settings.payday_first = validated_first
    settings.payday_second = validated_second

    db.session.add(settings)
    return settings


def get_commitment_for_user(user, commitment_id: int) -> FinanceCommitment:
    """Busca um compromisso do usuário autenticado sem risco de cross-user."""
    if user is None:
        raise ValueError("Usuário obrigatório.")
    commitment = FinanceCommitment.query.filter_by(id=commitment_id, user_id=user.id).first()
    if commitment is None:
        raise RuntimeError("Compromisso não encontrado para este usuário.")
    return commitment


def create_commitment(user, *, name: str, amount, due_date, kind: str, is_paid: bool = False) -> FinanceCommitment:
    """Cria um compromisso financeiro do usuário autenticado."""
    if user is None:
        raise ValueError("Usuário obrigatório.")

    normalized_name = (name or "").strip()
    if not normalized_name:
        raise ValueError("O nome do compromisso é obrigatório.")

    if kind not in {"fixed", "variable"}:
        raise ValueError("kind deve ser 'fixed' ou 'variable'.")

    if due_date is None:
        raise ValueError("A data de vencimento é obrigatória.")

    if isinstance(due_date, datetime):
        due_date = due_date.date()
    elif isinstance(due_date, str):
        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("due_date deve estar no formato YYYY-MM-DD.") from exc
    elif not isinstance(due_date, date):
        raise ValueError("due_date deve ser uma data válida.")

    if not isinstance(is_paid, bool):
        raise ValueError("is_paid deve ser booleano.")

    normalized_amount = parse_money(amount, field_name="valor do compromisso")
    if normalized_amount <= Decimal("0.00"):
        raise ValueError("O valor do compromisso deve ser maior que zero.")

    commitment = FinanceCommitment(
        user_id=user.id,
        name=normalized_name,
        amount=normalized_amount,
        due_date=due_date,
        kind=kind,
        is_paid=is_paid,
    )
    db.session.add(commitment)
    return commitment


def mark_commitment_paid(commitment: FinanceCommitment, *, is_paid: bool = True) -> FinanceCommitment:
    """Marca ou desmarca um compromisso como pago."""
    if commitment is None:
        raise ValueError("Compromisso obrigatório.")

    commitment.is_paid = bool(is_paid)
    db.session.add(commitment)
    return commitment


def delete_commitment(commitment: FinanceCommitment) -> None:
    """Remove um compromisso do usuário autenticado."""
    if commitment is None:
        raise ValueError("Compromisso obrigatório.")
    db.session.delete(commitment)
