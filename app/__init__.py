from flask import Flask, render_template
from app.common.utils import to_sao_paulo_time

from app.auth.models import User
from app.auth.routes import auth_bp
from app.body.routes import body_bp
from app.workouts.routes import workouts_bp
from app.config import Config
from app.dashboard.routes import dashboard_bp
from app.extensions import db, login_manager, migrate
from app.finance.routes import finance_bp
from app.goals.models import Goal
from app.goals.routes import goals_bp
from app.quick_log.models import QuickLog
from app.quick_log.routes import quick_log_bp


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    app.jinja_env.filters["sao_paulo_time"] = to_sao_paulo_time

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(body_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(quick_log_bp)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500

    return app
