"""
Cart service.

Implements a simple session-based cart where items are stored as a
mapping of product_id -> quantity. The service also provides methods
to compute totals and expose a structured cart summary.
"""

from flask import session

from ..models import Product


class CartService:
    """
    Business logic for cart operations on top of Flask's session.
    """

    SESSION_KEY = "cart"
    LOW_STOCK_THRESHOLD = 5

    @classmethod
    def _get_raw_cart(cls) -> dict:
        """
        Retrieve the raw cart dict from the session.
        """
        return session.get(cls.SESSION_KEY, {})

    @classmethod
    def _save_raw_cart(cls, cart: dict):
        """
        Save the raw cart back to the session.
        """
        session[cls.SESSION_KEY] = cart
        # Mark session as modified so Flask knows to persist it.
        session.modified = True

    @classmethod
    def add_item(cls, product_id: int, qty: int = 1):
        """
        Add an item to the cart, increasing quantity if it already exists.
        """
        if qty <= 0:
            return

        cart = cls._get_raw_cart()
        current_qty = cart.get(str(product_id), 0)
        cart[str(product_id)] = current_qty + qty
        cls._save_raw_cart(cart)

    @classmethod
    def update_item(cls, product_id: int, qty: int):
        """
        Update the quantity of an item in the cart.

        If qty <= 0, the item is removed.
        """
        cart = cls._get_raw_cart()
        key = str(product_id)

        if qty <= 0:
            if key in cart:
                del cart[key]
        else:
            cart[key] = qty

        cls._save_raw_cart(cart)

    @classmethod
    def remove_item(cls, product_id: int):
        """
        Remove an item from the cart entirely.
        """
        cart = cls._get_raw_cart()
        cart.pop(str(product_id), None)
        cls._save_raw_cart(cart)

    @classmethod
    def clear(cls):
        """
        Clear the entire cart.
        """
        cls._save_raw_cart({})

    @classmethod
    def _stock_status(cls, product: Product) -> str:
        """
        Determine the stock status label for a given product.
        """
        if product.qty <= 0:
            return "out_of_stock"
        if product.qty <= cls.LOW_STOCK_THRESHOLD:
            return "low_stock"
        return "in_stock"

    @classmethod
    def get_cart_summary(cls) -> dict:
        """
        Build a structured representation of the cart contents.

        Returns a dict with:
        - items: list of item dicts
        - total_cents: integer total
        - item_count: number of distinct items
        """
        cart = cls._get_raw_cart()
        if not cart:
            return {"items": [], "total_cents": 0, "item_count": 0}

        product_ids = [int(pid) for pid in cart.keys()]

        # Fetch active products only
        products = Product.query.filter(
            Product.id.in_(product_ids),
            Product.status == "active",
        ).all()

        products_by_id = {p.id: p for p in products}

        items = []
        total_cents = 0

        for pid_str, qty in cart.items():
            pid = int(pid_str)
            product = products_by_id.get(pid)

            if not product:
                # Product may have been deleted or archived; skip it
                continue

            qty = max(1, int(qty))
            unit_price = product.price_cents
            subtotal = unit_price * qty

            total_cents += subtotal

            items.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "qty": qty,
                "unit_price_cents": unit_price,
                "subtotal_cents": subtotal,
                "stock_available": product.qty,
                "stock_status": cls._stock_status(product),
                "image_url": product.image_url,
            })

        return {
            "items": items,
            "total_cents": total_cents,
            "item_count": len(items),
        }
