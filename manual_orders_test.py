"""
Manual order routes test.

Run with:
    python manual_orders_test.py

This script:
  - ensures a sample product exists,
  - registers/logs in a test user via HTTP endpoints,
  - adds product to cart,
  - performs checkout (retrying if payment randomly fails),
  - lists orders,
  - fetches order details,
  - cancels a pending order,
  - fetches details again to confirm status change.
"""

from app import create_app
from app.extensions import db
from app.models import Category, Product


def ensure_sample_product_id(app) -> int:
    """
    Ensure there is at least one active product for testing.

    Returns:
        int: product_id to be used in tests
    """
    with app.app_context():
        product = Product.query.filter_by(status="active").first()
        if product:
            return product.id

        category = Category.query.filter_by(name="Orders Test Category").first()
        if not category:
            category = Category(
                name="Orders Test Category",
                description="Category for manual order tests",
            )
            db.session.add(category)
            db.session.flush()

        product = Product(
            name="Orders Test Product",
            sku="ORD-TEST-001",
            description="A product used to test order routes.",
            price_cents=1500,
            qty=10,
            category=category,
            status="active",
        )
        db.session.add(product)
        db.session.commit()

        # Return only the ID, not the instance itself
        return product.id


def register_and_login(client, email="orderuser@example.com", password="pass123"):
    """
    Register (if necessary) and log in a user via HTTP endpoints.
    """
    # Try to register; ignore error if email already exists
    client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )

    # Login
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    print("[LOGIN]", resp.status_code, resp.get_json())
    return resp


def create_order_via_checkout(client, product_id: int):
    """
    Add a product to cart and attempt checkout.

    Because payment is random, we retry a few times until we succeed
    or hit a limit.
    """
    # Clear cart at start
    client.post("/cart/clear")

    # Add product to cart
    resp = client.post(f"/cart/add/{product_id}", json={"qty": 2})
    print("[ADD TO CART]", resp.status_code, resp.get_json())

    # Review checkout
    resp = client.get("/checkout")
    print("[CHECKOUT REVIEW]", resp.status_code, resp.get_json())

    # Try checkout up to 5 times in case of random payment failure
    for attempt in range(1, 6):
        resp = client.post("/checkout")
        data = resp.get_json()
        print(f"[CHECKOUT ATTEMPT {attempt}]", resp.status_code, data)

        if resp.status_code == 200 and data.get("success"):
            print("[CHECKOUT SUCCESS]")
            return data.get("order_id")

        print("[CHECKOUT FAILED, RETRYING]")

    print("[CHECKOUT] Gave up after 5 attempts.")
    return None


def run_order_tests(app):
    """
    Drive the full order flow for manual testing.
    """
    product_id = ensure_sample_product_id(app)
    print(f"Using product_id={product_id}")

    client = app.test_client()

    # Register and login
    register_and_login(client)

    # Initially list orders (likely empty)
    resp = client.get("/orders")
    print("\n[ORDERS LIST - INITIAL]", resp.status_code, resp.get_json())

    # Create an order via checkout
    order_id = create_order_via_checkout(client, product_id)
    if not order_id:
        print("Could not create a successful order, aborting further tests.")
        return

    # List orders after checkout
    resp = client.get("/orders")
    print("\n[ORDERS LIST - AFTER CHECKOUT]", resp.status_code, resp.get_json())

    # Get details of the created order
    resp = client.get(f"/orders/{order_id}")
    print("\n[ORDER DETAIL - BEFORE CANCEL]", resp.status_code, resp.get_json())

    # Attempt to cancel the order
    resp = client.post(f"/orders/{order_id}/cancel")
    print("\n[ORDER CANCEL]", resp.status_code, resp.get_json())

    # Get details of the order again
    resp = client.get(f"/orders/{order_id}")
    print("\n[ORDER DETAIL - AFTER CANCEL]", resp.status_code, resp.get_json())


if __name__ == "__main__":
    app = create_app()
    run_order_tests(app)
