"""
Flask application factory for the ecommerce project.

This module creates and configures the Flask application instance.
Extensions like the database are initialized here, and routes or
blueprints are attached in a controlled order.
"""

from flask import Flask

from .config import get_config
from .extensions import db
from .utils.admin_seed import seed_admin
from .routes.auth import auth_bp
from .routes.shop import shop_bp
from .routes.cart import cart_bp
from .routes.checkout import checkout_bp
from .routes.orders import orders_bp
from .routes.admin_products import admin_products_bp
from .routes.admin_users import admin_users_bp
from .routes.admin_orders import admin_orders_bp


def create_app():
    """
    Application factory.

    Creates and configures the Flask application instance. This pattern
    supports testing, modularity, and a clean initialization sequence.
    """
    app = Flask(__name__)
    app.config.from_object(get_config())

    register_extensions(app)

    # Database tables and seeded admin
    with app.app_context():
        # Temporary: create all tables for early development.
        # Later this will be replaced by proper migrations.
        db.create_all()
        seed_admin()

    register_routes(app)

    return app


def register_extensions(app):
    """
    Initialize Flask extensions with the application context.

    At this stage we only have SQLAlchemy. Other extensions like
    migration tools will be added in later commits.
    """
    db.init_app(app)


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

    @app.get("/")
    def index():
        return "Ecommerce backend is running with auth, catalog, cart, checkout, orders, and admin products."
