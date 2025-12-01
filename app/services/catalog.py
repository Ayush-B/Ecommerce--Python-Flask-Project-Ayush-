"""
Catalog service.

Provides product listing, filtering, sorting, and detail retrieval.
The service isolates business logic from route handlers.
"""

from ..models import Product, Category
from sqlalchemy import asc, desc


class CatalogService:
    """
    Business logic for product browsing and searching.
    """

    @staticmethod
    def list_products(
        page: int = 1,
        per_page: int = 12,
        search: str = None,
        category: str = None,
        sort: str = None,
    ):
        """
        Return a paginated list of products with optional search,
        category filtering, and sorting.

        Sorting options:
        - "newest" (default)
        - "price_asc"
        - "price_desc"
        """
        query = Product.query.filter_by(status="active")

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Product.name.ilike(pattern) |
                Product.description.ilike(pattern)
            )

        if category:
            query = query.join(Category).filter(Category.name == category)

        # Sorting
        if sort == "price_asc":
            query = query.order_by(asc(Product.price_cents))
        elif sort == "price_desc":
            query = query.order_by(desc(Product.price_cents))
        else:
            # default sort: newest
            query = query.order_by(desc(Product.created_at))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        products = [p.to_dict() for p in pagination.items]

        return {
            "products": products,
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
        }

    @staticmethod
    def get_product(product_id: int):
        """
        Retrieve a single active product by ID.
        """
        return Product.query.filter_by(id=product_id, status="active").first()
