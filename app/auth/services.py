from flask import abort

from app.auth.models import User
from app.extensions import db


def create_user(email: str, password: str, name: str) -> User:
    email = email.strip().lower()
    password = password.strip()
    name = name.strip()

    if not email or not password or not name:
        raise ValueError("Email, senha e nome são obrigatórios.")

    if User.query.filter_by(email=email).first():
        raise ValueError("Este e-mail já está cadastrado.")

    user = User(email=email)
    user.set_password(password)
    user.is_active = True
    db.session.add(user)
    db.session.flush()

    from app.auth.models import UserProfile

    profile = UserProfile(user_id=user.id, name=name)
    db.session.add(profile)
    db.session.commit()

    return user


def get_user_by_email(email: str):
    return User.query.filter_by(email=email.strip().lower()).first()


def get_user_by_id(user_id: int):
    return User.query.get(user_id)
