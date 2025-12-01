"""
ActivityLog model.

Tracks administrative actions performed in the system so that changes
to products, users, orders, and other entities can be audited.
"""

from datetime import datetime

from ..extensions import db
from .base import BaseModel


class ActivityLog(BaseModel):
    """
    Represents a single admin action in the system.

    This model records which administrator performed an action, what
    type of action it was, which target entity it affected, and any
    additional details relevant for auditing.
    """

    __tablename__ = "activity_log"

    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    admin = db.relationship("User", backref="activity_logs")

    action_type = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(100), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)

    # Explicit timestamp for the logged action, separate from created_at
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    # Free-form details: may contain JSON-encoded text or a simple message.
    details = db.Column(db.Text)

    def to_dict(self) -> dict:
        """
        Serialize the log entry for display in admin interfaces or APIs.
        """
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_email": self.admin.email if self.admin else None,
            "action_type": self.action_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "details": self.details,
        }
