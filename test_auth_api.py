import requests

BASE_URL = "http://127.0.0.1:5000"


def register_user(email: str, password: str):
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password},
    )
    print("REGISTER:", resp.status_code, resp.json())


def login_user(email: str, password: str):
    session = requests.Session()
    resp = session.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
    )
    print("LOGIN:", resp.status_code, resp.json())
    return session


def get_profile(session: requests.Session):
    resp = session.get(f"{BASE_URL}/auth/profile")
    print("PROFILE:", resp.status_code, resp.json())


def update_profile(session: requests.Session):
    resp = session.post(
        f"{BASE_URL}/auth/profile",
        json={
            "address_line": "123 Main St",
            "city": "Test City",
            "state": "TS",
            "postal_code": "12345",
            "country": "USA",
        },
    )
    print("UPDATE PROFILE:", resp.status_code, resp.json())


if __name__ == "__main__":
    # Make sure your Flask app is already running: python run.py
    email = "test1@example.com"
    password = "pass123"

    register_user(email, password)
    session = login_user(email, password)
    get_profile(session)
    update_profile(session)
    get_profile(session)
