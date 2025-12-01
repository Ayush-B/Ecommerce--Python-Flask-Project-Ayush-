"""
Manual checkout test script.

Run with:
    python manual_checkout_test.py

This script performs:
  - user registration and login via auth routes,
  - cart creation via cart routes,
  - checkout review and processing via /checkout endpoints,
  - inspection of the resulting order in the database.
"""

from app import create_app
from app.extensions import db
from app.models import User, Category, Product, Order, OrderItem
from app.extensions import db


TEST_USER_EMAIL = "checkout_test@example.com"
TEST_USER_PASSWORD = "testpass123"


def ensure_sample_product():
    """
    Ensure there is at least one active product in the database.

    Returns the product instance used for checkout tests.
    """
    product = Product.query.filter_by(status="active").first()
    if product:
        return product

    # Create a default category if none exists
    category = Category.query.filter_by(name="Checkout Test Category").first()
    if not category:
        category = Category(
            name="Checkout Test Category",
            description="Category used for manual checkout tests",
        ).save(commit=False)

    # Create a sample product
    product = Product(
        name="Checkout Test USB Cable",
        sku="CHK-USB-001",
        description="A test USB cable product for checkout testing.",
        price_cents=1299,
        qty=50,
        category=category,
        status="active",
        image_url=None,
    )
    db.session.add(product)
    db.session.commit()

    return product


def run_checkout_tests(app):
    """
    Run a full checkout scenario using Flask's test_client.
    """
    with app.app_context():
        product = ensure_sample_product()
        product_id = product.id
        print(f"Using product id={product_id}, name={product.name}")

    client = app.test_client()

    # 1) Register user (if not already registered)
    print("\n[1] POST /auth/register")
    resp = client.post(
        "/auth/register",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    print("Status:", resp.status_code, "Body:", resp.get_json())

    # 2) Login
    print("\n[2] POST /auth/login")
    resp = client.post(
        "/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    print("Status:", resp.status_code, "Body:", resp.get_json())

    if resp.status_code != 200:
        print("Login failed, aborting checkout test.")
        return

    # 3) Clear any existing cart
    print("\n[3] POST /cart/clear")
    resp = client.post("/cart/clear")
    print("Status:", resp.status_code, "Body:", resp.get_json())

    # 4) Add product to cart
    print("\n[4] POST /cart/add/<id> with qty=2")
    resp = client.post(f"/cart/add/{product_id}", json={"qty": 2})
    print("Status:", resp.status_code, "Body:", resp.get_json())

    # 5) Checkout review
    print("\n[5] GET /checkout (review)")
    resp = client.get("/checkout")
    print("Status:", resp.status_code, "Body:", resp.get_json())

    # 6) Process checkout
    print("\n[6] POST /checkout (process)")
    resp = client.post("/checkout")
    data = resp.get_json()
    print("Status:", resp.status_code, "Body:", data)

    if resp.status_code != 200 or not data or not data.get("success"):
        print("\nCheckout did not succeed. This may be a simulated payment failure.")
        return

    order_id = data["order_id"]

    # 7) Inspect the created order directly from the database
    with app.app_context():
        order = db.session.get(Order, order_id)
        if not order:
            print(f"\nOrder with id {order_id} not found in database.")
            return

        print("\n[7] Order found in database:")
        print("  id:", order.id)
        print("  user_id:", order.user_id)
        print("  status:", order.status)
        print("  total_cents:", order.total_cents)
        print("  placed_at:", order.placed_at)

        print("  Items:")
        for item in order.items:
            print(
                "   - product_id:", item.product_id,
                "qty:", item.qty,
                "unit_price_cents:", item.unit_price_cents,
                "subtotal_cents:", item.subtotal_cents,
            )

        # Check stock reduction
        product = db.session.get(Product, product_id)
        print("\n[8] Product stock after checkout:")
        print("  product_id:", product.id)
        print("  name:", product.name)
        print("  remaining qty:", product.qty)


if __name__ == "__main__":
    app = create_app()
    run_checkout_tests(app)
