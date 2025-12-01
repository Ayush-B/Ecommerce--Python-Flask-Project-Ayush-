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
    Attach simple placeholder routes.

    Full blueprints for shop, auth, and admin will be added in later commits.
    """

    @app.get("/")
    def index():
        return "Ecommerce app is running. Database and User model are initialized."