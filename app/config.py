"""
Configuration module for the ecommerce application.

This file centralizes configuration logic so the application
factory can load settings cleanly depending on the environment.
"""

import os


class BaseConfig:
    """Base configuration shared across environments."""

    DEBUG = False
    TESTING = False

    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    pass


def get_config():
    """Select the configuration class based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")

    if env == "production":
        return ProductionConfig
    if env == "testing":
        return TestingConfig
    return DevelopmentConfig
