"""
Admin product management routes.

Supports both JSON API (for tests/scripts) and HTML forms (for the admin UI).
"""

from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
)

from ..models import Product, Category
from ..utils.auth_decorators import admin_required

admin_products_bp = Blueprint("admin_products", __name__, url_prefix="/admin/products")


@admin_products_bp.get("/")
@admin_required
def list_products():
    """
    Admin product list.

    - ?format=json or JSON Accept header → JSON list
    - default (browser) → HTML table
    """
    products = Product.query.order_by(Product.created_at.desc()).all()

    if request.args.get("format") == "json" or (
        request.accept_mimetypes["application/json"]
        > request.accept_mimetypes["text/html"]
    ):
        return jsonify([p.to_dict() for p in products])

    return render_template("admin/products/list.html", products=products)


@admin_products_bp.get("/new")
@admin_required
def new_product_page():
    """
    Render HTML form to create a product.
    """
    return render_template("admin/products/new.html")


@admin_products_bp.post("/")
@admin_required
def create_product():
    """
    Create a product.

    - JSON body (tests/scripts) → JSON response
    - HTML form POST → redirect back to product list
    """
    data = request.get_json(silent=True) or request.form

    name = data.get("name")
    sku = data.get("sku")
    description = data.get("description")
    price_raw = data.get("price")
    qty_raw = data.get("qty")
    category_name = data.get("category")
    image_url = data.get("image_url")

    if not name or not sku:
        # For HTML, you might later add flash + redirect, but for now JSON error is fine
        return jsonify({"error": "Name and SKU are required"}), 400

    try:
        price_cents = int(float(price_raw or 0) * 100)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid price value"}), 400

    try:
        qty = int(qty_raw or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid quantity value"}), 400

    category_obj = None
    if category_name:
        category_obj = Category.query.filter_by(name=category_name).first()
        if not category_obj:
            category_obj = Category(name=category_name, description="").save()

    product = Product(
        name=name,
        sku=sku,
        description=description,
        price_cents=price_cents,
        qty=qty,
        category=category_obj,
        image_url=image_url,
        status="active",
    )
    product.save()

    # JSON clients
    if request.args.get("format") == "json" or request.is_json:
        return jsonify({"message": "Product created", "product": product.to_dict()}), 201

    # HTML clients → back to list
    return redirect(url_for("admin_products.list_products"))


@admin_products_bp.get("/<int:product_id>/edit")
@admin_required
def edit_product_page(product_id):
    """
    Render HTML form to edit an existing product.
    """
    product = Product.query.get_or_404(product_id)
    return render_template("admin/products/edit.html", product=product)


@admin_products_bp.post("/<int:product_id>")
@admin_required
def update_product(product_id):
    """
    Update a product.

    - JSON body → JSON response
    - HTML form POST → redirect to product list
    """
    product = Product.query.get_or_404(product_id)

    data = request.get_json(silent=True) or request.form

    name = data.get("name")
    sku = data.get("sku")
    description = data.get("description")
    price_raw = data.get("price")
    qty_raw = data.get("qty")
    category_name = data.get("category")
    image_url = data.get("image_url")

    if not name or not sku:
        return jsonify({"error": "Name and SKU are required"}), 400

    try:
        price_cents = int(float(price_raw or 0) * 100)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid price value"}), 400

    try:
        qty = int(qty_raw or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid quantity value"}), 400

    category_obj = None
    if category_name:
        category_obj = Category.query.filter_by(name=category_name).first()
        if not category_obj:
            category_obj = Category(name=category_name, description="").save()

    product.name = name
    product.sku = sku
    product.description = description
    product.price_cents = price_cents
    product.qty = qty
    product.category = category_obj
    product.image_url = image_url

    product.save()

    if request.args.get("format") == "json" or request.is_json:
        return jsonify({"message": "Product updated", "product": product.to_dict()})

    return redirect(url_for("admin_products.list_products"))


@admin_products_bp.post("/<int:product_id>/archive")
@admin_required
def archive_product(product_id):
    """
    Archive a product (status = 'archived') instead of hard deleting it.
    """
    product = Product.query.get_or_404(product_id)
    product.status = "archived"
    product.save()

    if request.args.get("format") == "json" or request.is_json:
        return jsonify({"message": "Product archived", "product": product.to_dict()})

    return redirect(url_for("admin_products.list_products"))
