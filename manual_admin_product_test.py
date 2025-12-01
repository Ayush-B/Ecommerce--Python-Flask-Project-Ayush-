"""
Manual admin product management test.

Run with:
    python manual_admin_products_test.py

This script:
  - logs in as the seeded admin user (from .env),
  - creates a new product,
  - lists admin products,
  - edits the product,
  - archives the product,
  - lists products again with status filter.
"""

import os

from dotenv import load_dotenv

from app import create_app

load_dotenv(override=True)


def login_admin(client):
    """
    Log in as the seeded admin using ADMIN_EMAIL / ADMIN_PASSWORD from .env.
    """
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        print("ADMIN_EMAIL or ADMIN_PASSWORD not set in .env; cannot run admin tests.")
        return None

    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    print("[ADMIN LOGIN]", resp.status_code, resp.get_json())
    return resp


def run_admin_product_tests(app):
    client = app.test_client()

    # 1) Log in as admin
    login_resp = login_admin(client)
    if not login_resp or login_resp.status_code != 200:
        print("Admin login failed; aborting admin product tests.")
        return

    # 2) Create a new product
    new_product_payload = {
        "name": "Admin Test Product",
        "sku": "ADMIN-TEST-001",
        "description": "Product created via admin test script.",
        "price_cents": 2500,
        "qty": 15,
        "category_name": "Admin Test Category",
        "status": "active",
        "image_url": "http://example.com/image.png",
    }

    resp = client.post("/admin/products/new", json=new_product_payload)
    print("\n[CREATE PRODUCT]", resp.status_code)
    create_data = resp.get_json()
    print(create_data)

    if resp.status_code != 201:
        print("Failed to create product; aborting further tests.")
        return

    product_id = create_data["product"]["id"]

    # 3) List products (admin view)
    resp = client.get("/admin/products")
    print("\n[LIST PRODUCTS]", resp.status_code)
    print(resp.get_json())

    # 4) Edit the product (change price and qty)
    edit_payload = {
        "price_cents": 3000,
        "qty": 5,
        "description": "Updated description from admin test.",
    }
    resp = client.post(f"/admin/products/{product_id}/edit", json=edit_payload)
    print("\n[EDIT PRODUCT]", resp.status_code)
    print(resp.get_json())

    # 5) Archive the product
    resp = client.post(f"/admin/products/{product_id}/delete")
    print("\n[ARCHIVE PRODUCT]", resp.status_code)
    print(resp.get_json())

    # 6) List only archived products
    resp = client.get("/admin/products?status=archived")
    print("\n[LIST ARCHIVED PRODUCTS]", resp.status_code)
    print(resp.get_json())


if __name__ == "__main__":
    app = create_app()
    run_admin_product_tests(app)
