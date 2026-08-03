# app/routes.py
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import jwt
import os
from app.models import db, User, Post
from app.utils import (
    logger,
    record_request_metrics,
    record_auth_attempt,
    record_error,
    http_requests_total
)

# Create blueprint
bp = Blueprint("api", __name__, url_prefix="/api")

# INTENTIONAL VULNERABILITY: Hardcoded secret (GitLeaks will catch this)
SECRET_KEY_HARDCODED = "my-super-secret-key-12345"

# ============================================================================
# HEALTH & METRICS ENDPOINTS (NO VULNERABILITIES)
# ============================================================================

@bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

@bp.route("/metrics", methods=["GET"])
def metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return generate_latest(), 200, {"Content-Type": "text/plain; version=0.0.4"}

# ============================================================================
# USER ENDPOINTS
# ============================================================================

@bp.route("/users", methods=["GET"])
def list_users():
    """
    List all users.
    INTENTIONAL VULNERABILITY: No pagination, no filtering — could leak all user data.
    """
    try:
        users = User.query.all()
        return jsonify([{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "created_at": u.created_at.isoformat()
        } for u in users]), 200
    except Exception as e:
        record_error("database_error", str(e))
        # INTENTIONAL VULNERABILITY: Exposing raw exception message (info disclosure)
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """Fetch user by ID."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
            "is_active": user.is_active
        }), 200
    except Exception as e:
        record_error("database_error", str(e))
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@bp.route("/users", methods=["POST"])
def create_user():
    """
    Create a new user.
    INTENTIONAL VULNERABILITIES:
    - No input validation (accepts any username/email format)
    - Weak password hashing (SHA256, should be bcrypt)
    """
    try:
        data = request.get_json()
        
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "Missing username or password"}), 400
        
        # INTENTIONAL: No validation on email format, username length, password strength
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"error": "User already exists"}), 409
        
        user = User(username=username, email=email)
        user.set_password(password)  # INTENTIONAL: Uses SHA256 instead of bcrypt
        
        db.session.add(user)
        db.session.commit()
        
        record_auth_attempt(True)
        logger.info(f"User created: {username}")
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        record_error("database_error", str(e))
        return jsonify({"error": f"Database error: {str(e)}"}), 500

# ============================================================================
# AUTHENTICATION ENDPOINT
# ============================================================================

@bp.route("/auth/login", methods=["POST"])
def login():
    """
    Login endpoint.
    INTENTIONAL VULNERABILITIES:
    - Uses hardcoded SECRET_KEY (should come from secure secrets manager)
    - No rate limiting on login attempts
    - No JWT expiration validation in some cases
    """
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            record_auth_attempt(False)
            return jsonify({"error": "Missing username or password"}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            record_auth_attempt(False)
            return jsonify({"error": "Invalid username or password"}), 401
        
        # INTENTIONAL: Using hardcoded SECRET_KEY instead of env var
        token = jwt.encode(
            {
                "user_id": user.id,
                "username": user.username,
                "exp": datetime.utcnow() + timedelta(hours=24)
            },
            SECRET_KEY_HARDCODED,  # VULNERABILITY: Should be env var
            algorithm="HS256"
        )
        
        record_auth_attempt(True)
        logger.info(f"User logged in: {username}")
        
        return jsonify({
            "token": token,
            "user_id": user.id,
            "username": user.username
        }), 200
    
    except Exception as e:
        record_error("auth_error", str(e))
        return jsonify({"error": f"Auth error: {str(e)}"}), 500

# ============================================================================
# VULNERABLE ENDPOINT: SQL INJECTION
# ============================================================================

@bp.route("/users/search", methods=["GET"])
def search_users_vulnerable():
    """
    INTENTIONAL VULNERABILITY: SQL Injection via user input
    
    This endpoint is deliberately vulnerable. A user can inject SQL:
    Example: /users/search?username=admin' OR '1'='1
    
    In Phase 5, Semgrep will catch this, and we'll fix it using parameterized queries.
    """
    try:
        username_query = request.args.get("username", "")
        
        # INTENTIONAL VULNERABILITY: String concatenation in SQL query
        # DO NOT do this in production!
        query = f"SELECT id, username, email FROM users WHERE username LIKE '%{username_query}%'"
        
        logger.warning(f"Executing raw SQL query: {query}")
        
        # Execute raw SQL (this is the vulnerability)
        result = db.session.execute(db.text(query))
        users = result.fetchall()
        
        return jsonify([{
            "id": u[0],
            "username": u[1],
            "email": u[2]
        } for u in users]), 200
    
    except Exception as e:
        record_error("sql_injection_attempt", str(e))
        # INTENTIONAL: Leaking SQL error details
        return jsonify({"error": f"Database error: {str(e)}"}), 500

# ============================================================================
# POST ENDPOINTS
# ============================================================================

@bp.route("/posts", methods=["GET"])
def list_posts():
    """List all posts."""
    try:
        posts = Post.query.all()
        return jsonify([{
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "user_id": p.user_id,
            "created_at": p.created_at.isoformat()
        } for p in posts]), 200
    except Exception as e:
        record_error("database_error", str(e))
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@bp.route("/posts", methods=["POST"])
def create_post():
    """Create a new post."""
    try:
        data = request.get_json()
        
        title = data.get("title")
        content = data.get("content")
        user_id = data.get("user_id")
        
        if not all([title, content, user_id]):
            return jsonify({"error": "Missing title, content, or user_id"}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        post = Post(title=title, content=content, user_id=user_id)
        db.session.add(post)
        db.session.commit()
        
        logger.info(f"Post created: {title} by user {user_id}")
        
        return jsonify({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "user_id": post.user_id,
            "created_at": post.created_at.isoformat()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        record_error("database_error", str(e))
        return jsonify({"error": f"Database error: {str(e)}"}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500