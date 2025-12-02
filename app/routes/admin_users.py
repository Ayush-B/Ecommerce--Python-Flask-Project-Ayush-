"""
Admin user management routes.

Provides:
- GET  /admin/users                     : list users (paginated)
- POST /admin/users/<id>/toggle_active  : activate/deactivate a user
- POST /admin/users/<id>/set_role       : change a user's role

Business rules:
- Cannot deactivate or demote the seeded admin.
- Cannot deactivate the currently logged-in admin.
"""

import json
import os

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from sqlalchemy import desc

from ..extensions import db
from ..models import User, ActivityLog
from ..utils.auth_decorators import admin_required

admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/admin/users")


def _get_seeded_admin_email() -> str | None:
    """
    Return the seeded admin email from environment, if any.
    """
    return os.getenv("ADMIN_EMAIL")


def _is_seeded_admin(user: User) -> bool:
    """
    Determine if the given user is the seeded admin.
    """
    seeded_email = _get_seeded_admin_email()
    return seeded_email is not None and user.email == seeded_email


def _is_current_admin(user: User) -> bool:
    """
    Check whether the given user is the currently logged-in admin.
    """
    current_user_id = session.get("user_id")
    return current_user_id is not None and user.id == current_user_id


def _log_admin_action(action_type: str, target_id: int, details: dict):
    """
    Create an ActivityLog entry for an admin action on a user.
    """
    admin_id = session.get("user_id")
    log = ActivityLog(
        admin_id=admin_id,
        action_type=action_type,
        target_type="User",
        target_id=target_id,
        details=json.dumps(details),
    )
    db.session.add(log)


@admin_users_bp.get("/")
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    seeded_admin_email = os.getenv("ADMIN_EMAIL")

    if request.args.get("format") == "json" or (
        request.accept_mimetypes["application/json"]
        > request.accept_mimetypes["text/html"]
    ):
        return jsonify([u.to_dict() for u in users])

    return render_template(
        "admin/users/list.html",
        users=users,
        seeded_admin=seeded_admin_email,
    )


@admin_users_bp.post("/<int:user_id>/toggle_active")
@admin_required
def toggle_active(user_id):
    """
    Activate or deactivate a user.

    Rules:
    - Cannot deactivate the seeded admin.
    - Cannot deactivate the currently logged-in admin (self).
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if _is_seeded_admin(user):
        return jsonify({"error": "Cannot change active status of seeded admin"}), 400

    if _is_current_admin(user):
        return jsonify({"error": "Cannot deactivate your own account"}), 400

    previous = user.is_active
    user.is_active = not user.is_active
    db.session.add(user)

    _log_admin_action(
        action_type="user_toggle_active",
        target_id=user.id,
        details={"previous": previous, "new": user.is_active},
    )

    db.session.commit()

    return jsonify({"message": "User active status updated", "user": user.to_dict()})


@admin_users_bp.post("/<int:user_id>/set_role")
@admin_required
def set_role(user_id):
    """
    Change a user's role.

    JSON body:
    - role: expected 'customer' or 'admin'

    Rules:
    - Cannot change role of seeded admin.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json or {}
    new_role = data.get("role")

    if new_role not in ("customer", "admin"):
        return jsonify({"error": "Invalid role, must be 'customer' or 'admin'"}), 400

    if _is_seeded_admin(user):
        return jsonify({"error": "Cannot change role of seeded admin"}), 400

    previous = user.role
    user.role = new_role
    db.session.add(user)

    _log_admin_action(
        action_type="user_set_role",
        target_id=user.id,
        details={"previous": previous, "new": new_role},
    )

    db.session.commit()

    return jsonify({"message": "User role updated", "user": user.to_dict()})
