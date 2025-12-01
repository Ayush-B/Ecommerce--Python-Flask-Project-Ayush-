"""
Authentication routes: register, login, logout, and profile management.
"""

from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from ..models import User
from ..extensions import db
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


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Log the user out.

    - If called from an API client (expects JSON), return JSON.
    - If called from a normal browser link, redirect to home.
    """
    session.clear()

    # If the client clearly prefers JSON, return JSON
    if request.is_json or (
        request.accept_mimetypes["application/json"]
        > request.accept_mimetypes["text/html"]
    ):
        return jsonify({"message": "Logged out"})

    # Default HTML behavior
    return redirect(url_for("shop.home"))


@auth_bp.get("/profile")
@login_required
def profile():
    user = User.query.get(session["user_id"])
    return render_template("auth/profile.html", user=user)


@auth_bp.post("/profile/update")
@login_required
def update_profile():
    user = User.query.get(session["user_id"])

    name = request.form.get("name")
    address_line = request.form.get("address_line")
    city = request.form.get("city")
    state = request.form.get("state")
    postal_code = request.form.get("postal_code")
    country = request.form.get("country")

    if not name:
        flash("Name cannot be empty.", "error")
        return redirect(url_for("auth.profile"))

    user.name = name  # assuming you add this column as above
    user.address_line = address_line
    user.city = city
    user.state = state
    user.postal_code = postal_code
    user.country = country

    db.session.commit()

    flash("Profile updated successfully.", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.post("/profile/password")
@login_required
def update_password():
    user = User.query.get(session["user_id"])

    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")

    if not old_password or not new_password:
        flash("Both password fields are required.", "error")
        return redirect(url_for("auth.profile"))

    # Use the User model's check_password method
    if not user.check_password(old_password):
        flash("Old password is incorrect.", "error")
        return redirect(url_for("auth.profile"))

    # Use the User model's set_password method
    user.set_password(new_password)
    db.session.commit()

    flash("Password updated successfully.", "success")
    return redirect(url_for("auth.profile"))

