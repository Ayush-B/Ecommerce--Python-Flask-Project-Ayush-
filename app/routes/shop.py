"""
Public catalog browsing routes: product listing, filters, and detail view.
"""

from flask import Blueprint, request, jsonify, render_template

from ..services.catalog import CatalogService
from ..models import Category

shop_bp = Blueprint("shop", __name__)


@shop_bp.get("/")
def home():
    """
    Storefront home page: hero + featured products.
    """
    data = CatalogService.list_products(
        page=1,
        per_page=8,
        search=None,
        category=None,
        sort="newest",
    )
    featured_products = data.get("products", [])

    return render_template("home.html", featured_products=featured_products)


@shop_bp.get("/products")
def products():
    """
    Product list with pagination, search, category filter, and sorting.

    Query parameters:
      - page
      - search
      - category
      - sort: newest, price_asc, price_desc
      - format=json (optional) to get JSON instead of HTML.
    """
    page = request.args.get("page", default=1, type=int)
    search = request.args.get("search")
    category = request.args.get("category")
    sort = request.args.get("sort")

    data = CatalogService.list_products(
        page=page,
        per_page=12,
        search=search,
        category=category,
        sort=sort,
    )

    # Optional JSON API
    if request.args.get("format") == "json":
        return jsonify(data)

    # Get list of categories for the filter dropdown
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "shop/products.html",
        products=data.get("products", []),
        page=data.get("page", page),
        pages=data.get("pages", 1),
        total=data.get("total", 0),
        search=search or "",
        category_filter=category or "",
        sort=sort or "newest",
        categories=categories,
    )


@shop_bp.get("/product/<int:product_id>")
def product_detail(product_id):
    """
    Product detail page.

    - Normal use: renders HTML page.
    - With ?format=json: returns JSON representation.
    """
    product = CatalogService.get_product(product_id)

    if not product:
        if request.args.get("format") == "json":
            return jsonify({"error": "Product not found"}), 404
        # Simple HTML 404 for now
        return render_template("errors/404.html"), 404

    if request.args.get("format") == "json":
        return jsonify(product.to_dict())

    return render_template("shop/product_detail.html", product=product)
