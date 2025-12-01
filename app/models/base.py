"""
Base model definition for the ecommerce project.

All ORM models will inherit from BaseModel to share common fields and
helper methods. This keeps each individual model focused on its own
domain properties.
"""

from datetime import datetime

from ..extensions import db


class BaseModel(db.Model):
    """
    Base model with common columns and helper methods.

    Every table in the project will have an integer primary key and
    timestamps for creation and last update. The save and delete methods
    wrap common session operations so calling code stays concise.
    """

    __abstract__ = True  # SQLAlchemy will not create a table for this class.

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def save(self, commit: bool = True):
        """
        Add the current instance to the session and optionally commit.

        Using this helper avoids repeating db.session.add/commit everywhere.
        """
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit: bool = True):
        """
        Remove the current instance from the session and optionally commit.
        """
        db.session.delete(self)
        if commit:
            db.session.commit()

    def to_dict(self) -> dict:
        """
        Convert the model instance to a plain dictionary.

        Subclasses are expected to override this method so that each model
        controls how it is serialized.
        """
        raise NotImplementedError("Subclasses must implement to_dict()")
