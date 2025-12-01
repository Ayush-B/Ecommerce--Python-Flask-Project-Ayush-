"""
Admin product management routes.

Provides:
- GET  /admin/products              : list products (with optional status filter)
- POST /admin/products/new          : create a new product
- POST /admin/products/<id>/edit    : edit an existing product
- POST /admin/products/<id>/delete  : archive a product (soft delete)
"""

import json
from flask import Blueprint, request, jsonify, session
from sqlalchemy import desc

from ..extensions import db
from ..models import Product, Category, ActivityLog
from ..utils.auth_decorators import admin_required

admin_products_bp = Blueprint("admin_products", __name__, url_prefix="/admin/products")


def _get_or_create_category(name: str) -> Category:
    """
    Find a category by name or create it if it does not exist.
    """
    category = Category.query.filter_by(name=name).first()
    if category:
        return category

    category = Category(name=name, description=f"Category {name}")
    db.session.add(category)
    db.session.flush()
    return category


def _log_admin_action(action_type: str, target_type: str, target_id: int, details: dict):
    """
    Create an ActivityLog entry for an admin action.
    """
    admin_id = session.get("user_id")
    log = ActivityLog(
        admin_id=admin_id,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        details=json.dumps(details),
    )
    db.session.add(log)


@admin_products_bp.get("")
@admin_required
def list_products():
    """
    List products for admin.

    Query parameters:
    - page (int, default 1)
    - status (optional, e.g. 'active', 'archived', 'deleted')
    """
    page = request.args.get("page", default=1, type=int)
    status = request.args.get("status")
    per_page = 12

    query = Product.query.order_by(desc(Product.created_at))

    if status:
        query = query.filter_by(status=status)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = [p.to_dict() for p in pagination.items]

    return jsonify(
        {
            "products": products,
            "page": pagination.page,
            "pages": pagination.pages,
            "total": pagination.total,
        }
    )


@admin_products_bp.post("/new")
@admin_required
def create_product():
    """
    Create a new product.

    Expected JSON body:
    - name (str, required)
    - sku (str, required, unique)
    - description (str, optional)
    - price_cents (int, required)
    - qty (int, required)
    - category_name (str, optional)
    - status (str, optional, default 'active')
    - image_url (str, optional)
    """
    data = request.json or {}

    name = data.get("name")
    sku = data.get("sku")
    price_cents = data.get("price_cents")
    qty = data.get("qty")

    if not name or not sku or price_cents is None or qty is None:
        return jsonify({"error": "name, sku, price_cents, and qty are required"}), 400

    try:
        price_cents = int(price_cents)
        qty = int(qty)
    except (ValueError, TypeError):
        return jsonify({"error": "price_cents and qty must be integers"}), 400

    if Product.query.filter_by(sku=sku).first():
        return jsonify({"error": "SKU already exists"}), 400

    category = None
    category_name = data.get("category_name")
    if category_name:
        category = _get_or_create_category(category_name)

    product = Product(
        name=name,
        sku=sku,
        description=data.get("description"),
        price_cents=price_cents,
        qty=qty,
        category=category,
        status=data.get("status", "active"),
        image_url=data.get("image_url"),
    )

    db.session.add(product)
    db.session.flush()

    _log_admin_action(
        action_type="product_create",
        target_type="Product",
        target_id=product.id,
        details=data,
    )

    db.session.commit()

    return jsonify({"message": "Product created", "product": product.to_dict()}), 201


@admin_products_bp.post("/<int:product_id>/edit")
@admin_required
def edit_product(product_id):
    """
    Edit an existing product.

    JSON body may include:
    - name
    - description
    - price_cents
    - qty
    - category_name
    - status
    - image_url
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.json or {}

    if "name" in data:
        product.name = data["name"]
    if "description" in data:
        product.description = data["description"]
    if "price_cents" in data:
        try:
            product.price_cents = int(data["price_cents"])
        except (ValueError, TypeError):
            return jsonify({"error": "price_cents must be integer"}), 400
    if "qty" in data:
        try:
            product.qty = int(data["qty"])
        except (ValueError, TypeError):
            return jsonify({"error": "qty must be integer"}), 400
    if "status" in data:
        product.status = data["status"]
    if "image_url" in data:
        product.image_url = data["image_url"]
    if "category_name" in data and data["category_name"]:
        category = _get_or_create_category(data["category_name"])
        product.category = category

    db.session.add(product)

    _log_admin_action(
        action_type="product_edit",
        target_type="Product",
        target_id=product.id,
        details=data,
    )

    db.session.commit()

    return jsonify({"message": "Product updated", "product": product.to_dict()})


@admin_products_bp.post("/<int:product_id>/delete")
@admin_required
def delete_product(product_id):
    """
    Archive a product (soft delete) by setting its status to 'archived'.

    This keeps the product in the database so existing orders remain valid.
    """
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Soft delete: mark as archived
    previous_status = product.status
    product.status = "archived"

    db.session.add(product)

    details = {"previous_status": previous_status, "new_status": "archived"}
    _log_admin_action(
        action_type="product_archive",
        target_type="Product",
        target_id=product.id,
        details=details,
    )

    db.session.commit()

    return jsonify({"message": "Product archived", "product": product.to_dict()})
