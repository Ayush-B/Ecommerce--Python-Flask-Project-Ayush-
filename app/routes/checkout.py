"""
Checkout routes.

GET /checkout  : view cart summary before checkout
POST /checkout : run checkout with async payment simulation
"""

import asyncio
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session

from ..services.cart import CartService
from ..services.checkout import CheckoutService
from ..models import User

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@checkout_bp.get("")
def checkout_review():
    """
    Checkout review.

    - If ?format=json is provided, return JSON summary (used by tests / API).
    - Otherwise, render HTML review page.
    """
    summary = CartService.get_cart_summary()

    # JSON API mode preserved
    if request.args.get("format") == "json":
        return jsonify(summary)

    # Empty cart → send user back to cart page
    if summary["item_count"] == 0:
        return redirect(url_for("cart.view_cart_page"))

    # Load user (if logged in) to show shipping details
    user = None
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)

    return render_template("checkout/review.html", cart=summary, user=user)


@checkout_bp.post("")
def checkout_process():
    """
    Begin checkout, run async payment, and return order result (JSON).
    """
    # TEMPORARY: allow checkout without login for UI testing.
    # When auth UI is in place, we will restore login_required
    # and use session["user_id"].
    user_id = session.get("user_id") or 1  # seeded admin or test user

    # Run the async checkout logic
    result = asyncio.run(CheckoutService.process_checkout(user_id))

    if not result["success"]:
        return jsonify({"error": result["error"]}), 400

    return jsonify(result)
