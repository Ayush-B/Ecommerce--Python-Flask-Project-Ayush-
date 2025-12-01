"""
Models package.

This package groups all ORM models. The BaseModel provides shared fields
and helper methods, while concrete models define domain-specific data.
"""

from .base import BaseModel
from .user import User

__all__ = ["BaseModel", "User"]
