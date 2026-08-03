# app/__init__.py
from flask import Flask
from flask import request
from flask_cors import CORS
from app.config import active_config
from app.models import db
from app.utils import logger, http_requests_total
from datetime import datetime
import time

def create_app(config=None):
    """
    Application factory function.
    
    Args:
        config: Configuration object (defaults to active_config from environment)
    
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = active_config
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)  # Enable CORS for all routes
    
    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
    
    # Request/response middleware for metrics
    @app.before_request
    def before_request():
        """Record request start time."""
        app.request_start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Record request metrics after response."""
        if hasattr(app, 'request_start_time'):
            duration = time.time() - app.request_start_time
            http_requests_total.labels(
                method=request.method,
                endpoint=request.path,
                status=response.status_code
            ).inc()
            logger.info(
                f"{request.method} {request.path} -> {response.status_code} ({duration:.3f}s)"
            )
        return response
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        logger.warning(f"Bad request: {str(e)}")
        return {"error": "Bad request"}, 400
    
    @app.errorhandler(404)
    def not_found(e):
        logger.warning(f"Not found: {str(e)}")
        return {"error": "Endpoint not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {str(e)}")
        return {"error": "Internal server error"}, 500
    
    logger.info(f"Flask app initialized with config: {config.__class__.__name__}")
    
    return app