"""
Admin seeding logic.

This module ensures the initial administrator exists. The email and
password come from environment variables. This step simplifies early
development and ensures the admin cannot accidentally be removed.
"""

import os

from ..extensions import db
from ..models import User


def seed_admin():
    """
    Ensure the initial admin user exists.

    If an admin with the configured email already exists, the function
    does nothing. Or it creates one using the password from the
    environment.
    """
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        print("[Admin Seed] Skipped. Missing ADMIN_EMAIL or ADMIN_PASSWORD.")
        return

    existing = User.query.filter_by(email=admin_email).first()
    if existing:
        print("[Admin Seed] Admin already exists.")
        return

    admin = User(
        email=admin_email,
        role="admin",
        is_active=True,
    )
    admin.set_password(admin_password)
    admin.save()

    print(f"[Admin Seed] Created initial administrator: {admin_email}")
