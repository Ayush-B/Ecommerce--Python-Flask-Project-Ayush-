from dotenv import load_dotenv
load_dotenv(override=True)

from app import create_app
from app.extensions import db
from app.models import User, Product, Order, OrderItem

app = create_app()

with app.app_context():
    user = User.query.first()
    product = Product.query.first()

    order = Order(user_id=user.id, status="pending")
    item = OrderItem(
        order=order,
        product=product,
        unit_price_cents=product.price_cents,
        qty=2,
        subtotal_cents=product.price_cents * 2,
    )

    order.items.append(item)
    order.calculate_total()
    order.save()

    print("Created order:", order.to_dict())
