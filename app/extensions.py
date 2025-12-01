"""
Application-wide extensions.

This module holds instances of objects like the database connection,
so they can be initialized with the application inside the factory.
"""

from flask_sqlalchemy import SQLAlchemy

# The SQLAlchemy instance will be initialized with the app in create_app.
db = SQLAlchemy()
