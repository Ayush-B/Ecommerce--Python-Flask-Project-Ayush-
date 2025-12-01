"""
Entry point for running the ecommerce Flask application.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Running in development mode, configured via FLASK_ENV
    app.run(host="127.0.0.1", port=5000)
