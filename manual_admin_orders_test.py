"""
Manual admin order management test.

Run with:
    python manual_admin_orders_test.py

This script:
  - ensures a product and a customer exist,
  - creates an order via the public checkout flow (retrying on payment failures),
  - logs in as admin,
  - lists all orders,
  - views a specific order,
  - changes status to 'shipped',
  - attempts to cancel a shipped order (should fail),
  - creates another order and cancels it as admin to confirm stock restoration.
"""

import os

from dotenv import load_dotenv

from app import create_app
from app.extensions import db
from app.models import Category, Product

load_dotenv(override=True)


def ensure_sample_product_id(app) -> int:
    """
    Ensure at least one active product with decent stock exists.

    Returns:
        product_id (int)
    """
    with app.app_context():
        product = Product.query.filter_by(status="active").first()
        if product:
            return product.id

        category = Category.query.filter_by(name="Admin Orders Test Category").first()
        if not category:
            category = Category(
                name="Admin Orders Test Category",
                description="Category for admin order tests",
            )
            db.session.add(category)
            db.session.flush()

        product = Product(
            name="Admin Orders Test Product",
            sku="ADMIN-ORD-TEST-001",
            description="Product used for admin order tests.",
            price_cents=2000,
            qty=50,
            category=category,
            status="active",
        )
        db.session.add(product)
        db.session.commit()

        return product.id


def register_and_login_customer(app, email="order-customer@example.com", password="pass123"):
    """
    Create a customer account via HTTP (if needed) and log in.
    """
    client = app.test_client()

    # Try registration; if already exists, ignore error
    client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )

    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    print("[CUSTOMER LOGIN]", resp.status_code, resp.get_json())
    return client


def create_order_via_checkout(client, product_id: int):
    """
    Create an order via cart + checkout.

    Because payment is random, retry a few times.
    """
    # Clear cart
    client.post("/cart/clear")

    # Add to cart
    resp = client.post(f"/cart/add/{product_id}", json={"qty": 2})
    print("[ADD TO CART]", resp.status_code, resp.get_json())

    # Review checkout
    resp = client.get("/checkout")
    print("[CHECKOUT REVIEW]", resp.status_code, resp.get_json())

    # Try checkout up to 5 times
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


def login_admin(app):
    """
    Log in as seeded admin using ADMIN_EMAIL / ADMIN_PASSWORD.
    """
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        print("ADMIN_EMAIL or ADMIN_PASSWORD not set; cannot run admin order tests.")
        return None

    client = app.test_client()
    resp = client.post("/auth/login", json={"email": email, "password": password})
    print("[ADMIN LOGIN]", resp.status_code, resp.get_json())
    if resp.status_code != 200:
        return None
    return client


def run_admin_order_tests(app):
    # Get a product_id instead of a Product object
    product_id = ensure_sample_product_id(app)

    # If you want to show the name as well, fetch it inside a context:
    with app.app_context():
        product = Product.query.get(product_id)
        print(f"Using product id={product.id}, name={product.name}")

    # 1) Create an order as a customer
    customer_client = register_and_login_customer(app)
    order_id = create_order_via_checkout(customer_client, product_id)
    if not order_id:
        print("Could not create a customer order; aborting admin order tests.")
        return

    # 2) Log in as admin
    admin_client = login_admin(app)
    if not admin_client:
        print("Admin login failed; aborting admin order tests.")
        return

    # 3) List all orders
    resp = admin_client.get("/admin/orders")
    print("\n[ADMIN ORDERS LIST]", resp.status_code)
    print(resp.get_json())

    # 4) View details of the created order
    resp = admin_client.get(f"/admin/orders/{order_id}")
    print("\n[ADMIN ORDER DETAIL - INITIAL]", resp.status_code)
    print(resp.get_json())

    # 5) Change status to 'shipped'
    resp = admin_client.post(
        f"/admin/orders/{order_id}/change_status",
        json={"status": "shipped"},
    )
    print("\n[ADMIN CHANGE STATUS TO SHIPPED]", resp.status_code)
    print(resp.get_json())

    # 6) Attempt to cancel the shipped order (should fail)
    resp = admin_client.post(
        f"/admin/orders/{order_id}/change_status",
        json={"status": "canceled"},
    )
    print("\n[ADMIN ATTEMPT CANCEL SHIPPED ORDER]", resp.status_code)
    print(resp.get_json())

    # 7) Create another order and cancel it to test stock restoration
    new_order_id = create_order_via_checkout(customer_client, product_id)
    if not new_order_id:
        print("Could not create second order for cancel test.")
        return

    # View before cancel
    resp = admin_client.get(f"/admin/orders/{new_order_id}")
    print("\n[SECOND ORDER DETAIL - BEFORE CANCEL]", resp.status_code)
    print(resp.get_json())

    resp = admin_client.post(
        f"/admin/orders/{new_order_id}/change_status",
        json={"status": "canceled"},
    )
    print("\n[ADMIN CHANGE STATUS TO CANCELED]", resp.status_code)
    print(resp.get_json())


if __name__ == "__main__":
    app = create_app()
    run_admin_order_tests(app)
