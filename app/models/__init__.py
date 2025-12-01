"""
Models package.

This package groups all ORM models used by the ecommerce application.
The BaseModel provides common fields and helpers that other models
inherit from.
"""

from .base import BaseModel

__all__ = ["BaseModel"]
