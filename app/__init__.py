from flask import Flask, render_template

from app.auth.models import User
from app.auth.routes import auth_bp
from app.config import Config
from app.dashboard.routes import dashboard_bp
from app.extensions import db, login_manager, migrate


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500

    return app
