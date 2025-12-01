"""
Order routes for regular users.

Provides:
- GET /orders         : list of user's orders (paginated)
- GET /orders/<id>    : details of a single order
- POST /orders/<id>/cancel : cancel a pending order
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from sqlalchemy import desc

from ..extensions import db
from ..models import Order, User
from ..utils.auth_decorators import login_required

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


def _user_can_access_order(order):
    """
    Check whether the current session user can access the given order.

    - A customer can only see their own orders.
    - An admin can see any order.
    """
    current_user_id = session.get("user_id")
    role = session.get("role")

    if role == "admin":
        return True

    return order.user_id == current_user_id


@orders_bp.get("/")
@login_required
def list_orders():
    """
    List orders.

    - Customers: only their own orders.
    - Admins: all orders.
    """
    user_id = session["user_id"]
    user = User.query.get(user_id)

    page = request.args.get("page", default=1, type=int)
    per_page = 10

    # Admin sees all orders, customer sees only theirs
    if user.role == "admin":
        base_query = Order.query
    else:
        base_query = Order.query.filter_by(user_id=user_id)

    pagination = (
        base_query
        .order_by(Order.placed_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    orders = pagination.items

    if request.args.get("format") == "json":
        return jsonify(
            {
                "orders": [o.to_dict() for o in orders],
                "page": pagination.page,
                "pages": pagination.pages,
                "total": pagination.total,
            }
        )

    return render_template(
        "orders/list.html",
        orders=orders,
        page=pagination.page,
        pages=pagination.pages,
        total=pagination.total,
    )


@orders_bp.get("/<int:order_id>")
@login_required
def order_detail(order_id):
    """
    Order detail.

    - Customers: only their own orders.
    - Admins: can view any order.
    """
    user_id = session["user_id"]
    user = User.query.get(user_id)

    if user.role == "admin":
        order = Order.query.filter_by(id=order_id).first()
    else:
        order = Order.query.filter_by(id=order_id, user_id=user_id).first()

    if not order:
        if request.args.get("format") == "json":
            return jsonify({"error": "Order not found"}), 404
        return "Order not found", 404

    if request.args.get("format") == "json":
        return jsonify(order.to_dict())

    return render_template("orders/detail.html", order=order)


@orders_bp.post("/orders/<int:order_id>/cancel")
@login_required
def cancel_order(order_id):
    """
    Cancel a pending order.

    Business rules:
      - Only 'pending' orders may be canceled.
      - A regular user may cancel only their own orders.
      - An admin may cancel any pending order.
      - When canceled, stock for each item is restored.
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if not _user_can_access_order(order):
        return jsonify({"error": "Forbidden"}), 403

    if order.status != "pending":
        return jsonify({"error": "Only pending orders can be canceled"}), 400

    # Restore stock for each item
    for item in order.items:
        if item.product:
            item.product.qty += item.qty
            db.session.add(item.product)

    order.status = "canceled"
    db.session.add(order)
    db.session.commit()

    return jsonify({"message": "Order canceled", "order": order.to_dict()})
