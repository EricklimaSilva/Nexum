from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.models import User
from app.auth.services import create_user, get_user_by_email
from app.common.validators import is_valid_email, sanitize_text
from app.extensions import limiter


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", key_func=lambda: current_user.get_id() if current_user.is_authenticated else request.remote_addr)
def login():
    if request.method == "POST":
        email = sanitize_text(request.form.get("email"))
        password = request.form.get("password", "")

        if not email or not password:
            flash("E-mail e senha são obrigatórios.", "error")
            return render_template("auth/login.html")

        if not is_valid_email(email):
            flash("Digite um e-mail válido.", "error")
            return render_template("auth/login.html")

        user = get_user_by_email(email)
        if user is None or not user.check_password(password):
            flash("Credenciais inválidas.", "error")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Usuário inativo.", "error")
            return render_template("auth/login.html")

        login_user(user)
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", key_func=lambda: current_user.get_id() if current_user.is_authenticated else request.remote_addr)
def register():
    if request.method == "POST":
        email = sanitize_text(request.form.get("email"))
        password = request.form.get("password", "")
        name = sanitize_text(request.form.get("name"))

        if not email or not password or not name:
            flash("Todos os campos são obrigatórios.", "error")
            return render_template("auth/register.html")

        if not is_valid_email(email):
            flash("Digite um e-mail válido.", "error")
            return render_template("auth/register.html")

        try:
            user = create_user(email, password, name)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("auth/register.html")

        login_user(user)
        flash("Conta criada com sucesso.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sessão.", "info")
    return redirect(url_for("auth.login"))
