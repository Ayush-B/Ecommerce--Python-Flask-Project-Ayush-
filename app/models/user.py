"""
User model for the ecommerce application.

A user may be a customer or an administrator. This model manages
authentication fields, roles, activation status, and shipping data.
"""

from ..extensions import db
from .base import BaseModel

from werkzeug.security import generate_password_hash, check_password_hash


class User(BaseModel):
    """
    Represents a registered user of the ecommerce system.

    The seeded administrator is also stored here. Passwords are stored
    as secure hashes rather than plain text for safety.
    """

    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(50), nullable=False, default="customer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # Shipping information
    address_line = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))

    def set_password(self, password: str):
        """
        Hash and store a user's password.

        The plaintext password is never stored, only the hash.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Validate a plaintext password against the stored hash.
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """
        Serialize essential fields for administrative displays.

        Sensitive fields like password_hash are intentionally excluded.
        """
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "city": self.city,
            "country": self.country,
        }
