"""
Checkout service.

Converts the session cart to an order, validates stock, deducts inventory,
and triggers asynchronous payment.
"""

from datetime import datetime, timedelta

from flask import session

from ..extensions import db
from ..models import Product, Order, OrderItem
from .payment import PaymentService
from .cart import CartService


class CheckoutService:
    """
    Main checkout workflow: validate, create order, process payment.
    """

    @staticmethod
    def _validate_stock(cart_items):
        """
        Validate all products in cart have enough stock.

        Raises ValueError if stock is insufficient.
        """
        for item in cart_items:
            product = Product.query.get(item["product_id"])
            if not product or product.status != "active":
                raise ValueError(f"Product {item['product_id']} is unavailable.")

            if product.qty < item["qty"]:
                raise ValueError(
                    f"Insufficient stock for product {product.id} ('{product.name}')."
                )

    @staticmethod
    def _deduct_stock(cart_items):
        """
        Deduct purchased quantities from product stock.
        """
        for item in cart_items:
            product = Product.query.get(item["product_id"])
            product.qty -= item["qty"]
            db.session.add(product)

    @staticmethod
    def _create_order(user_id, cart_summary):
        """
        Create the Order and OrderItems DB entries.
        """
        order = Order(
            user_id=user_id,
            status="pending",
            total_cents=cart_summary["total_cents"],
            placed_at=datetime.utcnow(),
        )
        db.session.add(order)
        db.session.flush()  # get order.id

        for item in cart_summary["items"]:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product_id"],
                unit_price_cents=item["unit_price_cents"],
                qty=item["qty"],
                subtotal_cents=item["subtotal_cents"],
            )
            db.session.add(order_item)

        return order

    @staticmethod
    def estimate_delivery_date():
        return datetime.utcnow() + timedelta(days=3)

    @staticmethod
    async def process_checkout(user_id):
        """
        Full checkout pipeline.

        Returns:
            dict with "success", "order" or "error".
        """
        cart_summary = CartService.get_cart_summary()

        if cart_summary["item_count"] == 0:
            return {"success": False, "error": "Cart is empty."}

        # Validate stock
        try:
            CheckoutService._validate_stock(cart_summary["items"])
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        # Create order
        order = CheckoutService._create_order(user_id, cart_summary)

        # Deduct stock
        CheckoutService._deduct_stock(cart_summary["items"])

        db.session.commit()

        # Process payment
        payment_success = await PaymentService.process_payment(
            amount_cents=cart_summary["total_cents"],
            user_id=user_id,
        )

        if not payment_success:
            # Payment failed, rollback by canceling order
            order.status = "canceled"
            db.session.add(order)
            db.session.commit()
            return {"success": False, "error": "Payment declined."}

        # Payment succeeded
        order.status = "paid"
        db.session.add(order)
        db.session.commit()

        # Clear cart
        CartService.clear()

        return {
            "success": True,
            "order_id": order.id,
            "total_cents": order.total_cents,
            "delivery_estimate": CheckoutService.estimate_delivery_date().isoformat(),
        }
