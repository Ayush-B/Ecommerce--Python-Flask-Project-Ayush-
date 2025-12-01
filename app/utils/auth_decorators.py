"""
Authentication decorators.

Provides login_required for user-only endpoints.
"""

from functools import wraps
from flask import session, redirect, jsonify


def login_required(view_func):
    """
    Ensure that a user is logged in before accessing a route.

    Uses Flask's session object to check for the presence of user_id.
    """
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return view_func(*args, **kwargs)

    return wrapped
