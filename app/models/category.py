"""
Category model.

Categories allow administrators to group products and enable catalog
filtering. Categories are stored in a simple lookup table.
"""

from ..extensions import db
from .base import BaseModel


class Category(BaseModel):
    """
    Represents a product category.

    Each category has a unique name and optional description.
    Administrators can add or modify categories.
    """

    __tablename__ = "categories"

    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }
