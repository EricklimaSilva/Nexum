from __future__ import annotations

from app.auth.services import create_user as create_auth_user
from app.goals.services import create_goal
from app.quick_log.services import create_quick_log


def make_user(email: str = "user@example.com", password: str = "Pass1234", name: str = "Usuário"):
    return create_auth_user(email, password, name)


def make_goal(user, *, title: str = "Meta de exemplo", description: str = "Descreve a meta", category: str = "personal"):
    return create_goal(user, title=title, description=description, category=category)


def make_quick_log(user, *, action: str = "Estudou 1 hora", category: str = "study", xp_awarded: int = 10):
    return create_quick_log(user, action=action, category=category, xp_awarded=xp_awarded)
