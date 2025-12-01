# scratch_order_test.py

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(override=True)

from app import create_app
from app.extensions import db
from app.models import User, ActivityLog

app = create_app()

with app.app_context():
    admin = User.query.filter_by(role="admin").first()
    if admin is None:
        raise RuntimeError("Admin user not found. Check ADMIN_EMAIL / ADMIN_PASSWORD in .env and seeding.")

    log = ActivityLog(
        admin_id=admin.id,
        action_type="create_product",
        target_type="Product",
        target_id=1,
        details='{"name": "USB Cable", "sku": "USB-001"}',
    ).save()

    print(ActivityLog.query.first().to_dict())
