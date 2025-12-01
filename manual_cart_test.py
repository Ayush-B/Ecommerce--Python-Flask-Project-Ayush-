"""
Manual cart test script.

Run with:
    python manual_cart_test.py

This script:
  - creates a sample category and product (if none exist),
  - exercises the cart endpoints using Flask's test_client,
  - prints JSON responses so you can see cart behavior.
"""

from app import create_app
from app.extensions import db
from app.models import Category, Product


def ensure_sample_product():
    """
    Ensure there is at least one active product in the database.

    Returns the product instance we will use for cart tests.
    """
    product = Product.query.filter_by(status="active").first()
    if product:
        return product

    # Create a default category if none exists
    category = Category.query.filter_by(name="Test Category").first()
    if not category:
        category = Category(
            name="Test Category",
            description="Category used for manual cart tests",
        ).save(commit=False)

    # Create a sample product
    product = Product(
        name="Test USB Cable",
        sku="TEST-USB-001",
        description="A test USB cable product for cart testing.",
        price_cents=999,
        qty=20,
        category=category,
        status="active",
        image_url=None,
    )
    db.session.add(product)
    db.session.commit()

    return product


def run_cart_tests(app):
    """
    Run a sequence of cart operations and print the JSON responses.
    """
    with app.app_context():
        product = ensure_sample_product()
        product_id = product.id
        print(f"Using product id={product_id}, name={product.name}")

    client = app.test_client()

    # 1) Start with an empty cart
    print("\n[1] GET /cart (initial, expected empty)")
    resp = client.get("/cart")
    print(resp.status_code, resp.get_json())

    # 2) Add product to cart
    print("\n[2] POST /cart/add/<id> with qty=2")
    resp = client.post(f"/cart/add/{product_id}", json={"qty": 2})
    print(resp.status_code, resp.get_json())

    # 3) View cart again
    print("\n[3] GET /cart (after adding)")
    resp = client.get("/cart")
    print(resp.status_code, resp.get_json())

    # 4) Update quantity to 5
    print("\n[4] POST /cart/update/<id> with qty=5")
    resp = client.post(f"/cart/update/{product_id}", json={"qty": 5})
    print(resp.status_code, resp.get_json())

    # 5) Remove the item
    print("\n[5] POST /cart/remove/<id>")
    resp = client.post(f"/cart/remove/{product_id}")
    print(resp.status_code, resp.get_json())

    # 6) Clear cart (should already be empty, but this is idempotent)
    print("\n[6] POST /cart/clear")
    resp = client.post("/cart/clear")
    print(resp.status_code, resp.get_json())


if __name__ == "__main__":
    app = create_app()
    run_cart_tests(app)
