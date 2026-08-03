# app.py
import os
from app import create_app

# Get environment (defaults to development)
env = os.getenv("FLASK_ENV", "development")

# Create Flask app instance
app = create_app()

if __name__ == "__main__":
    # Run the development server
    # In production, use gunicorn (configured in Dockerfile)
    app.run(
        host="0.0.0.0",  # Listen on all interfaces
        port=int(os.getenv("PORT", 5000)),
        debug=(env == "development")
    )