"""
Public catalog browsing routes: product listing, filters, and detail view.
"""

from flask import Blueprint, request, jsonify

from ..services.catalog import CatalogService

shop_bp = Blueprint("shop", __name__)


@shop_bp.get("/products")
def products():
    """
    Product list with pagination, search, category filter, and sorting.

    Query parameters:
      - page
      - search
      - category
      - sort: newest, price_asc, price_desc
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
    return jsonify(data)


@shop_bp.get("/product/<int:product_id>")
def product_detail(product_id):
    """
    Retrieve detail of a single product.
    """
    product = CatalogService.get_product(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict())
