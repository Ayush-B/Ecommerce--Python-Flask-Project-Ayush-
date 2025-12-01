"""
Manual admin user management test.

Run with:
    python manual_admin_users_test.py

This script:
  - logs in as the seeded admin user (from .env),
  - lists users,
  - creates a test user (via auth/register),
  - toggles the test user's active status,
  - sets the test user's role to admin,
  - verifies that seeded admin cannot be demoted or deactivated.
"""

import os

from dotenv import load_dotenv

from app import create_app

load_dotenv(override=True)


def login_admin(client):
    """
    Log in as the seeded admin using ADMIN_EMAIL / ADMIN_PASSWORD from .env.
    """
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        print("ADMIN_EMAIL or ADMIN_PASSWORD not set in .env; cannot run admin tests.")
        return None

    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    print("[ADMIN LOGIN]", resp.status_code, resp.get_json())
    return resp


def create_test_user(client, email="admin-user-test@example.com", password="test123"):
    """
    Create a regular user via the public registration endpoint.

    If the user already exists, we simply return.
    """
    resp = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    print("[CREATE TEST USER]", resp.status_code, resp.get_json())
    # Registration will 400 if email already exists, but that is fine.


def find_user_id_by_email(client, email):
    """
    Find a user id by email using the admin /admin/users listing.
    """
    resp = client.get("/admin/users")
    data = resp.get_json() or {}
    for user in data.get("users", []):
        if user.get("email") == email:
            return user.get("id")
    return None


def run_admin_user_tests(app):
    client = app.test_client()

    # 1) Log in as admin
    login_resp = login_admin(client)
    if not login_resp or login_resp.status_code != 200:
        print("Admin login failed; aborting admin user tests.")
        return

    # 2) List users initially
    resp = client.get("/admin/users")
    print("\n[USERS LIST - INITIAL]", resp.status_code)
    print(resp.get_json())

    # 3) Create a test user via public registration
    test_email = "admin-user-test@example.com"
    create_test_user(client, email=test_email)

    # 4) List users again and find test user id
    resp = client.get("/admin/users")
    data = resp.get_json()
    print("\n[USERS LIST - AFTER TEST USER CREATION]", resp.status_code)
    print(data)

    test_user_id = find_user_id_by_email(client, test_email)
    if not test_user_id:
        print("Could not find test user in admin list; aborting.")
        return

    print(f"Test user id={test_user_id}")

    # 5) Toggle active status for the test user
    resp = client.post(f"/admin/users/{test_user_id}/toggle_active")
    print("\n[TOGGLE ACTIVE - TEST USER]", resp.status_code)
    print(resp.get_json())

    # 6) Set role to 'admin' for the test user
    resp = client.post(
        f"/admin/users/{test_user_id}/set_role",
        json={"role": "admin"},
    )
    print("\n[SET ROLE - TEST USER TO ADMIN]", resp.status_code)
    print(resp.get_json())

    # 7) Confirm seeded admin protections
    seeded_email = os.getenv("ADMIN_EMAIL")
    if seeded_email:
        seeded_id = find_user_id_by_email(client, seeded_email)
        if seeded_id:
            print(f"\nSeeded admin user id={seeded_id}")

            # Attempt to deactivate seeded admin
            resp = client.post(f"/admin/users/{seeded_id}/toggle_active")
            print("[TOGGLE ACTIVE - SEEDED ADMIN]", resp.status_code)
            print(resp.get_json())

            # Attempt to change seeded admin role
            resp = client.post(
                f"/admin/users/{seeded_id}/set_role",
                json={"role": "customer"},
            )
            print("[SET ROLE - SEEDED ADMIN TO CUSTOMER]", resp.status_code)
            print(resp.get_json())
        else:
            print("Seeded admin not found in /admin/users listing.")
    else:
        print("ADMIN_EMAIL not set; cannot test seeded admin protections.")


if __name__ == "__main__":
    app = create_app()
    run_admin_user_tests(app)
