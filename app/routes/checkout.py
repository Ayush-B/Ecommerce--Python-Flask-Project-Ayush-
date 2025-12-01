"""
Checkout routes.

GET /checkout: view cart summary before checkout
POST /checkout: run checkout with async payment simulation
"""

import asyncio
from flask import Blueprint, jsonify, session

from ..services.cart import CartService
from ..services.checkout import CheckoutService
from ..utils.auth_decorators import login_required

checkout_bp = Blueprint("checkout", __name__)


@checkout_bp.get("/checkout")
@login_required
def checkout_review():
    """
    Return cart summary before checkout.
    """
    summary = CartService.get_cart_summary()
    return jsonify(summary)


@checkout_bp.post("/checkout")
@login_required
def checkout_process():
    """
    Begin checkout, run async payment, and return order result.
    """
    user_id = session["user_id"]

    # Run the async checkout logic
    result = asyncio.run(CheckoutService.process_checkout(user_id))

    if not result["success"]:
        return jsonify({"error": result["error"]}), 400

    return jsonify(result)
