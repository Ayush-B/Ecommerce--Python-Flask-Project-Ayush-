"""
Order and OrderItem models for the ecommerce application.

Orders track the overall purchase information for a user, while
OrderItem rows store the specific products, quantities, and prices
that were purchased at that time.
"""

from datetime import datetime

from ..extensions import db
from .base import BaseModel


# Order status values used throughout the application.
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_SHIPPED = "shipped"
ORDER_STATUS_CANCELED = "canceled"


class Order(BaseModel):
    """
    Represents a customer's order.

    The total_cents and item prices are stored as snapshots of the
    purchase values. They do not change if product prices change later.
    """

    __tablename__ = "orders"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", backref="orders")

    status = db.Column(db.String(50), nullable=False, default=ORDER_STATUS_PENDING)

    total_cents = db.Column(db.Integer, nullable=False, default=0)
    placed_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationship to order items
    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def calculate_total(self):
        """
        Recalculate total_cents from items.

        This is useful when building an order from cart data before saving.
        """
        self.total_cents = sum(item.subtotal_cents for item in self.items)

    def to_dict(self) -> dict:
        """
        Serialize order data including items, suitable for display in
        order history or admin screens.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "total_cents": self.total_cents,
            "placed_at": self.placed_at.isoformat() if self.placed_at else None,
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(BaseModel):
    """
    Line item within an order.

    Each row records which product was purchased, how many units, and
    the prices at the time of purchase. These values should not change
    even if the product is later updated.
    """

    __tablename__ = "order_items"

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    order = db.relationship("Order", back_populates="items")

    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    product = db.relationship("Product")

    unit_price_cents = db.Column(db.Integer, nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    subtotal_cents = db.Column(db.Integer, nullable=False)

    def to_dict(self) -> dict:
        """
        Serialize order item fields. Includes a minimal snapshot of
        product information to support display without extra queries.
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.name if self.product else None,
            "sku": self.product.sku if self.product else None,
            "unit_price_cents": self.unit_price_cents,
            "qty": self.qty,
            "subtotal_cents": self.subtotal_cents,
        }
