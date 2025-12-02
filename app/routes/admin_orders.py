"""
Admin order management routes.

Provides:
- GET  /admin/orders                   : list all orders (filterable by status)
- GET  /admin/orders/<id>              : view a specific order
- POST /admin/orders/<id>/change_status: change order status

Business rules:
- Allowed statuses: pending, paid, shipped, canceled.
- Shipped orders cannot be changed to canceled.
- When changing to 'canceled' from a non-canceled state, stock is restored.
"""

import json
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for

from ..extensions import db
from ..models import Order, ActivityLog, Product
from ..models.order import (
    ORDER_STATUS_PENDING,
    ORDER_STATUS_PAID,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_CANCELED,
)
from ..utils.auth_decorators import admin_required

admin_orders_bp = Blueprint("admin_orders", __name__, url_prefix="/admin/orders")

ALLOWED_STATUSES = {
    ORDER_STATUS_PENDING,
    ORDER_STATUS_PAID,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_CANCELED,
}


def _log_admin_action(action_type: str, target_id: int, details: dict):
    """
    Create an ActivityLog entry for an admin order action.
    """

    admin_id = session.get("user_id")
    log = ActivityLog(
        admin_id=admin_id,
        action_type=action_type,
        target_type="Order",
        target_id=target_id,
        details=json.dumps(details),
    )
    db.session.add(log)


@admin_orders_bp.get("/")
@admin_required
def list_orders():
    """
    Admin order list.

    - ?format=json → JSON
    - default     → HTML
    """
    page = request.args.get("page", type=int, default=1)
    per_page = 10

    pagination = (
        Order.query.order_by(Order.placed_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    orders = pagination.items

    if request.args.get("format") == "json" or (
        request.accept_mimetypes["application/json"]
        > request.accept_mimetypes["text/html"]
    ):
        return jsonify(
            {
                "orders": [o.to_dict() for o in orders],
                "page": pagination.page,
                "pages": pagination.pages,
                "total": pagination.total,
            }
        )

    return render_template(
        "admin/orders/list.html",
        orders=orders,
        page=pagination.page,
        pages=pagination.pages,
        total=pagination.total,
    )


@admin_orders_bp.get("/<int:order_id>")
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    if request.args.get("format") == "json" or (
        request.accept_mimetypes["application/json"]
        > request.accept_mimetypes["text/html"]
    ):
        return jsonify(order.to_dict())

    return render_template("admin/orders/detail.html", order=order)


@admin_orders_bp.post("/<int:order_id>/change_status")
@admin_required
def change_order_status(order_id):
    """
    Change an order's status.

    JSON body:
    - status: new status (pending, paid, shipped, canceled)

    Business rules:
    - Cannot set to an unsupported status.
    - Shipped orders cannot be changed to canceled.
    - When changing TO 'canceled' from any other status, stock is restored.
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.json or {}
    new_status = data.get("status")

    if new_status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400

    previous_status = order.status

    # Enforce that shipped orders cannot be canceled.
    if previous_status == ORDER_STATUS_SHIPPED and new_status == ORDER_STATUS_CANCELED:
        return jsonify({"error": "Cannot cancel a shipped order"}), 400

    # If changing to canceled and it was not already canceled, restore stock
    if new_status == ORDER_STATUS_CANCELED and previous_status != ORDER_STATUS_CANCELED:
        for item in order.items:
            if item.product:
                item.product.qty += item.qty
                db.session.add(item.product)

    order.status = new_status
    db.session.add(order)

    _log_admin_action(
        action_type="order_change_status",
        target_id=order.id,
        details={"previous": previous_status, "new": new_status},
    )

    db.session.commit()

    return jsonify({"message": "Order status updated", "order": order.to_dict()})
