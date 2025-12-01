"""
Entry point for running the ecommerce Flask application.
"""

from dotenv import load_dotenv
from app import create_app

# Load variables from .env into the environment
load_dotenv()

app = create_app()

if __name__ == "__main__":
    # Running in development mode, configured via FLASK_ENV
    app.run(host="127.0.0.1", port=5000)