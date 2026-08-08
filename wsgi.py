"""
WSGI entry point for gunicorn.
Creates and exposes the Flask app instance.
"""
from app import create_app

# Create the Flask app instance
app = create_app()

if __name__ == "__main__":
    app.run()