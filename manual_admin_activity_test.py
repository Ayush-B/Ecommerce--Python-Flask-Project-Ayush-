"""
Manual admin activity log test.

Run with:
    python manual_admin_activity_test.py

This script:
  - logs in as the seeded admin,
  - triggers a few admin actions (create/edit/archive product),
  - fetches paginated activity logs,
  - calls the streaming endpoint and reads a few events.
"""

import os
import itertools

from dotenv import load_dotenv

from app import create_app

load_dotenv(override=True)


def login_admin(client):
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        print("ADMIN_EMAIL or ADMIN_PASSWORD not set; cannot run admin activity tests.")
        return None

    resp = client.post("/auth/login", json={"email": email, "password": password})
    print("[ADMIN LOGIN]", resp.status_code, resp.get_json())
    if resp.status_code != 200:
        return None
    return resp


def trigger_admin_actions(client):
    """
    Trigger a few admin actions that will generate ActivityLog entries.
    """
    # Create a product
    create_payload = {
        "name": "Activity Test Product",
        "sku": "ACT-TEST-001",
        "description": "Product created to generate activity log entries.",
        "price_cents": 5000,
        "qty": 10,
        "category_name": "Activity Category",
        "status": "active",
        "image_url": None,
    }
    resp = client.post("/admin/products/new", json=create_payload)
    print("\n[CREATE PRODUCT]", resp.status_code)
    create_data = resp.get_json()
    print(create_data)

    if resp.status_code != 201:
        return None

    product_id = create_data["product"]["id"]

    # Edit the product
    edit_payload = {
        "price_cents": 5500,
        "qty": 8,
        "description": "Updated description for activity test.",
    }
    resp = client.post(f"/admin/products/{product_id}/edit", json=edit_payload)
    print("\n[EDIT PRODUCT]", resp.status_code)
    print(resp.get_json())

    # Archive the product
    resp = client.post(f"/admin/products/{product_id}/delete")
    print("\n[ARCHIVE PRODUCT]", resp.status_code)
    print(resp.get_json())

    return product_id


def fetch_activity_page(client, page=1):
    """
    Fetch a page of activity logs.
    """
    resp = client.get(f"/admin/activity?page={page}")
    print(f"\n[ACTIVITY LIST - PAGE {page}]", resp.status_code)
    data = resp.get_json()
    print(data)
    return data


def stream_activity(client, max_events=5):
    """
    Connect to the streaming endpoint and read a few events.
    """
    # Use buffered=False to stream generator output
    resp = client.get("/admin/activity/stream?last_id=0", buffered=False)
    print("\n[ACTIVITY STREAM - FIRST FEW EVENTS] status:", resp.status_code)

    # resp.response is an iterator over chunks from the generator
    for i, chunk in zip(range(max_events), resp.response):
        # Each chunk is raw bytes like b"data: {...}\n\n"
        print("STREAM EVENT CHUNK:", chunk.decode("utf-8").strip())
        # We break after max_events chunks to avoid an infinite loop.
    resp.close()


def run_activity_tests(app):
    client = app.test_client()

    # 1) Log in as admin
    if not login_admin(client):
        print("Admin login failed; aborting activity tests.")
        return

    # 2) Trigger admin actions to generate logs
    trigger_admin_actions(client)

    # 3) Fetch first page of activity logs
    data = fetch_activity_page(client, page=1)

    # 4) If there are logs, call the streaming endpoint and read a few events
    if data.get("total", 0) > 0:
        stream_activity(client, max_events=5)
    else:
        print("No activity logs found; streaming test skipped.")


if __name__ == "__main__":
    app = create_app()
    run_activity_tests(app)
