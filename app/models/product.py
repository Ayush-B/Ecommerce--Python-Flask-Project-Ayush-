"""
Product model for the ecommerce system.

Products belong to categories, have stock levels, and include pricing
data stored in integer cents to avoid floating point rounding issues.
"""

from ..extensions import db
from .base import BaseModel


class Product(BaseModel):
    """
    Product listed in the online store.

    Prices are stored in cents as integers to maintain precise
    calculations. Status determines whether the product is visible
    to customers.
    """

    __tablename__ = "products"

    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    price_cents = db.Column(db.Integer, nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=0)

    # Category relationship
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship("Category", back_populates="products")

    # Product status: active, archived, deleted
    status = db.Column(db.String(50), nullable=False, default="active")

    # Optional image URL pointing to external image URL
    image_url = db.Column(db.String(500))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "description": self.description,
            "price_cents": self.price_cents,
            "qty": self.qty,
            "status": self.status,
            "image_url": self.image_url,
            "category": self.category.name if self.category else None,
        }
