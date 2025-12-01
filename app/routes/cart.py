"""
Cart routes.

Expose endpoints for adding items to the cart, updating quantities,
removing items, clearing the cart, and viewing the cart contents.
"""

from flask import Blueprint, request, jsonify

from ..models import Product
from ..services.cart import CartService

cart_bp = Blueprint("cart", __name__)


@cart_bp.get("/cart")
def view_cart():
    """
    Return the current session cart summary.
    """
    summary = CartService.get_cart_summary()
    return jsonify(summary)


@cart_bp.post("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    """
    Add a product to the cart.

    Request JSON (optional):
    - qty: integer quantity to add (default 1)
    """
    product = Product.query.filter_by(id=product_id, status="active").first()
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.json or {}
    qty = data.get("qty", 1)

    try:
        qty = int(qty)
    except (ValueError, TypeError):
        return jsonify({"error": "Quantity must be an integer"}), 400

    if qty <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400

    CartService.add_item(product_id, qty)
    summary = CartService.get_cart_summary()
    return jsonify({"message": "Item added to cart", "cart": summary})


@cart_bp.post("/cart/update/<int:product_id>")
def update_cart_item(product_id):
    """
    Update quantity of a product in the cart.

    Request JSON:
    - qty: new quantity (if <= 0, the item is removed)
    """
    data = request.json or {}
    qty = data.get("qty")

    if qty is None:
        return jsonify({"error": "Quantity is required"}), 400

    try:
        qty = int(qty)
    except (ValueError, TypeError):
        return jsonify({"error": "Quantity must be an integer"}), 400

    CartService.update_item(product_id, qty)
    summary = CartService.get_cart_summary()
    return jsonify({"message": "Cart updated", "cart": summary})


@cart_bp.post("/cart/remove/<int:product_id>")
def remove_cart_item(product_id):
    """
    Remove a product from the cart, if present.
    """
    CartService.remove_item(product_id)
    summary = CartService.get_cart_summary()
    return jsonify({"message": "Item removed", "cart": summary})


@cart_bp.post("/cart/clear")
def clear_cart():
    """
    Clear the entire cart.
    """
    CartService.clear()
    summary = CartService.get_cart_summary()
    return jsonify({"message": "Cart cleared", "cart": summary})
