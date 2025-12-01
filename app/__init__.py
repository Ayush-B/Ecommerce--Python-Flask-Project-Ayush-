"""
Flask application factory for the ecommerce project.

The goal of this module is to create the Flask application cleanly,
load configuration, register extensions, and attach blueprints.

Only essential functionality is implemented at this stage. Database
setup, blueprints, and services will be added in later commits.
"""

from flask import Flask
from .config import get_config


def create_app():
    """
    Application factory.

    Creates and configures the Flask application instance. This pattern
    supports testing, modularity, and a clean initialization sequence.
    """
    app = Flask(__name__)
    app.config.from_object(get_config())

    register_routes(app)

    return app


def register_routes(app):
    """
    Attach simple placeholder routes.

    Full blueprints for shop, auth, and admin will be added in later commits.
    """
    @app.get("/")
    def index():
        return "Ecommerce app is running. Blueprints will be added in later commits."

