"""
Flask application factory for the ecommerce project.

This module creates and configures the Flask application instance.
Extensions like the database are initialized here, and routes or
blueprints are attached in a controlled order.
"""

from flask import Flask, g, request
from datetime import datetime
from uuid import uuid4
import logging

from .config import get_config
from .extensions import db, login_manager
from .utils.admin_seed import seed_admin
from .routes.auth import auth_bp
from .routes.shop import shop_bp
from .routes.cart import cart_bp
from .routes.checkout import checkout_bp
from .routes.orders import orders_bp
from .routes.admin_products import admin_products_bp
from .routes.admin_users import admin_users_bp
from .routes.admin_orders import admin_orders_bp
from .routes.admin_activity import admin_activity_bp
from .logging_config import setup_logging

# Attempt to import your User model from common locations.
# If your User class lives in a different module, change the import path below.
try:
    # common path: app/models/user.py -> from .models.user import User
    from .models.user import User
except Exception:
    try:
        # alternate: app/models.py with class User
        from .models import User
    except Exception:
        User = None  # loader will return None if we can't import; prevents crash at startup


def create_app():
    """
    Application factory.
    """
    app = Flask(__name__)
    app.config.from_object(get_config())

    register_extensions(app)

    # set defaults if absent (can be overridden by config)
    app.config.setdefault("LOG_DIR", "logs")
    app.config.setdefault("LOG_FILE", "app.log")
    app.config.setdefault("LOG_LEVEL", "INFO")

    # Configure logging early so other initialization logs are captured.
    log_level = getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO)
    setup_logging(app,
                  log_dir=app.config["LOG_DIR"],
                  filename=app.config["LOG_FILE"],
                  level=log_level)
    app.logger.info("Logging configured")

    # Per-request ID for tracing across logs. RequestFilter reads g.request_id.
    @app.before_request
    def attach_request_id():
        g.request_id = request.headers.get("X-Request-ID") or uuid4().hex

    @app.after_request
    def add_request_id_header(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        return response

    # Database tables and seeded admin (development: create tables if needed)
    with app.app_context():
        db.create_all()
        seed_admin()

    register_routes(app)

    # Make now() available in all Jinja templates
    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow}

    return app


def register_extensions(app):
    """
    Initialize Flask extensions with the application context.
    """
    db.init_app(app)
    # initialize LoginManager so current_user works inside requests
    login_manager.init_app(app)
    # set the route name where unauthorized users are redirected (adjust to your auth blueprint)
    login_manager.login_view = "auth.login"

    # Register the user_loader for flask-login
    # This must be done after the User model is importable.
    @login_manager.user_loader
    def load_user(user_id):
        """
        Given a user_id (string) from the session, return the corresponding User object.
        Return None if not found or if the User import failed.
        """
        if not User:
            return None
        try:
            # user_id stored in session should be convertible to int in typical setups
            return User.query.get(int(user_id))
        except Exception:
            # If your User.get_id returns a string (UUID), adjust conversion accordingly:
            # return User.query.get(user_id)
            return None


def register_routes(app):
    """
    Attach blueprint and catalog routes and cart.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_products_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_orders_bp)
    app.register_blueprint(admin_activity_bp)

    @app.get("/health")
    def health():
        return "OK"

