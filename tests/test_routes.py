import pytest
import json
from app import create_app
from app.models import db, User, Post
from sqlalchemy.orm import Session


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    class TestingConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        JWT_SECRET_KEY = 'test-secret-key'
    
    app = create_app()
    app.config.from_object(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user for authentication tests."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    def get_user():
        with app.app_context():
            return db.session.get(User, user_id)
    
    return get_user


# ============================================================================
# HEALTH & METRICS TESTS (2 tests)
# ============================================================================

class TestHealthAndMetrics:
    """Test health check and metrics endpoints."""
    
    def test_health_endpoint(self, client):
        """Test GET /api/health returns healthy status."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_metrics_endpoint(self, client):
        """Test GET /api/metrics returns Prometheus metrics."""
        response = client.get('/api/metrics')
        assert response.status_code == 200
        assert b'http_requests_total' in response.data or b'HELP' in response.data


# ============================================================================
# AUTHENTICATION TESTS (3 tests)
# ============================================================================

class TestAuthentication:
    """Test login and authentication endpoints."""
    
    def test_login_success(self, client, test_user):
        """Test successful login returns JWT token."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        assert response.status_code == 200, f"Status: {response.status_code}, Response: {response.json}"
        data = response.json
        assert 'token' in data
        assert isinstance(data['token'], str)
        assert len(data['token']) > 0
    
    def test_login_invalid_username(self, client):
        """Test login with non-existent username returns 401."""
        response = client.post('/api/auth/login', json={
            'username': 'nonexistent',
            'password': 'password123'
        })
        assert response.status_code == 401
        assert 'Invalid' in response.json['error']
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with wrong password returns 401."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
        assert 'Invalid' in response.json['error']


# ============================================================================
# USER CRUD TESTS (6 tests)
# ============================================================================

class TestUserCRUD:
    """Test user creation, retrieval, update, and deletion."""
    
    def test_create_user_success(self, client):
        """Test creating a new user returns 201."""
        response = client.post('/api/users', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass123'
        })
        assert response.status_code == 201
        data = response.json
        assert data['username'] == 'newuser'
        assert data['email'] == 'new@example.com'
        assert 'password' not in data
    
    def test_create_user_duplicate_username(self, client, test_user):
        """Test creating user with duplicate username returns 409."""
        response = client.post('/api/users', json={
            'username': 'testuser',
            'email': 'another@example.com',
            'password': 'password123'
        })
        assert response.status_code == 409
        assert 'already exists' in response.json['error']
    
    def test_get_all_users(self, client, test_user):
        """Test GET /api/users returns list of users."""
        response = client.get('/api/users')
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]['username'] == 'testuser'
    
    def test_get_user_by_id(self, client, test_user, app):
        """Test GET /api/users/<id> returns specific user."""
        user = test_user()
        response = client.get(f'/api/users/{user.id}')
        assert response.status_code == 200
        data = response.json
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@example.com'
    
    def test_get_user_not_found(self, client):
        """Test GET /api/users/<id> with invalid ID returns 404."""
        response = client.get('/api/users/99999')
        assert response.status_code == 404
        assert 'not found' in response.json['error']
    
    def test_update_user_success(self, client, test_user, app):
        """Test PATCH /api/users/<id> updates user details."""
        user = test_user()
        response = client.patch(f'/api/users/{user.id}', json={
            'email': 'newemail@example.com'
        })
        # Accept 200 or 201 depending on implementation
        assert response.status_code in [200, 201]
        data = response.json
        assert data['email'] == 'newemail@example.com'


# ============================================================================
# POST CRUD TESTS (3 tests) - REVISED FOR ACTUAL ENDPOINTS
# ============================================================================

class TestPostCRUD:
    """Test post creation, retrieval, and deletion via /api/posts endpoint."""
    
    def test_create_post_success(self, client, test_user, app):
        """Test creating a new post via /api/posts."""
        user = test_user()
        
        # Create post directly via /api/posts endpoint
        response = client.post('/api/posts', json={
            'title': 'Test Post',
            'content': 'This is a test post content.',
            'user_id': user.id
        })
        assert response.status_code == 201
        data = response.json
        assert data['title'] == 'Test Post'
        assert data['content'] == 'This is a test post content.'
    
    def test_get_post_by_id(self, client, test_user, app):
        """Test GET /api/posts/<id> returns specific post."""
        user = test_user()
        
        # Create a post
        create_response = client.post('/api/posts', json={
            'title': 'Specific Post',
            'content': 'Specific content',
            'user_id': user.id
        })
        assert create_response.status_code == 201
        post_id = create_response.json['id']
        
        # Get post
        response = client.get(f'/api/posts/{post_id}')
        assert response.status_code == 200
        data = response.json
        assert data['title'] == 'Specific Post'
        assert data['content'] == 'Specific content'
    
    def test_get_all_posts(self, client, test_user, app):
        """Test GET /api/posts returns list of posts."""
        user = test_user()
        
        # Create a post
        client.post('/api/posts', json={
            'title': 'Test Post',
            'content': 'Test content',
            'user_id': user.id
        })
        
        # Get all posts
        response = client.get('/api/posts')
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
        assert len(data) >= 1


# ============================================================================
# VULNERABILITY TESTS (2 tests)
# ============================================================================

class TestVulnerabilities:
    """Test intentional vulnerabilities for security awareness."""
    
    def test_sql_injection_endpoint_exists(self, client):
        """Test vulnerable SQL injection endpoint is accessible."""
        response = client.get('/api/users/search?username=test')
        assert response.status_code == 200
        data = response.json
        assert isinstance(data, list)
    
    def test_hardcoded_secret_in_routes(self, client):
        """Test that hardcoded secret exists (INTENTIONAL vulnerability for learning)."""
        from app.routes import SECRET_KEY_HARDCODED
        assert SECRET_KEY_HARDCODED == "my-super-secret-key-12345"


# ============================================================================
# ERROR HANDLING TESTS (2 tests)
# ============================================================================

class TestErrorHandling:
    """Test error responses and status codes."""
    
    def test_404_not_found(self, client):
        """Test 404 response for non-existent route."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_missing_required_fields(self, client):
        """Test 400 response for missing required JSON fields."""
        response = client.post('/api/users', json={
            'username': 'onlyusername'
        })
        assert response.status_code == 400
        assert 'required' in response.json['error'].lower() or 'missing' in response.json['error'].lower()


# ============================================================================
# BONUS: INPUT VALIDATION TESTS (1 test)
# ============================================================================

class TestInputValidation:
    """Test input validation and error handling."""
    
    def test_create_post_without_user_id(self, client):
        """Test POST /api/posts without user_id returns 400."""
        response = client.post('/api/posts', json={
            'title': 'Post without user',
            'content': 'This should fail'
        })
        # Should fail because user_id is required or invalid
        assert response.status_code in [400, 404]