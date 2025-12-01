"""
Authentication routes: register, login, logout, and profile management.
"""

from flask import Blueprint, request, session, jsonify, render_template
from ..extensions import db
from ..models import User
from ..utils.auth_decorators import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/register")
def register():
    """
    Register a new user with email and password.

    Required fields:
    - email
    - password
    """
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    user = User(email=email)
    user.set_password(password)
    user.role = "customer"
    user.save()

    return jsonify({"message": "User registered"}), 201


@auth_bp.post("/login")
def login():
    """
    Log the user in by verifying credentials and writing user_id to session.
    """
    data = request.json or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email, is_active=True).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = user.id
    session["role"] = user.role

    return jsonify({"message": "Logged in", "user_id": user.id})


@auth_bp.get("/login")
def login_page():
    return render_template("auth/login.html")


@auth_bp.get("/register")
def register_page():
    return render_template("auth/register.html")


@auth_bp.post("/logout")
def logout():
    """
    Clear the session and log out the user.
    """
    session.clear()
    return jsonify({"message": "Logged out"})


@auth_bp.get("/profile")
@login_required
def profile():
    """
    Retrieve the logged-in user's profile.
    """
    user = User.query.get(session["user_id"])
    return jsonify(user.to_dict())


@auth_bp.post("/profile")
@login_required
def update_profile():
    """
    Update user profile fields including shipping address.
    """
    user = User.query.get(session["user_id"])
    data = request.json or {}

    # Allowed profile fields
    fields = [
        "address_line",
        "city",
        "state",
        "postal_code",
        "country",
    ]

    for field in fields:
        if field in data:
            setattr(user, field, data[field])

    user.save()

    return jsonify({"message": "Profile updated", "profile": user.to_dict()})
