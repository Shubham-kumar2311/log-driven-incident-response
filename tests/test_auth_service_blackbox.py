"""
Black box tests for Authentication Service
Tests the API contract without knowing internal implementation details
"""
import pytest
import requests
from datetime import datetime, timedelta


class TestAuthServiceLoginBlackBox:
    """Black box tests for login functionality"""
    
    @pytest.fixture
    def cleanup_token(self):
        """Cleanup fixture if needed"""
        yield
    
    def test_valid_login_returns_success(self, api_client):
        """Test that valid credentials return success with token"""
        response = api_client.post(
            "auth",
            "/login",
            json={"username": "testuser", "password": "testpass123"},
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["token"] is not None
    
    def test_invalid_password_returns_401(self, api_client):
        """Test that invalid password returns 401 Unauthorized"""
        response = api_client.post(
            "auth",
            "/login",
            json={"username": "testuser", "password": "wrongpassword"},
            timeout=5
        )
        
        assert response.status_code == 401
        assert "error" in response.json() or "message" in response.json()
    
    def test_nonexistent_user_returns_401(self, api_client):
        """Test that non-existent user returns 401"""
        response = api_client.post(
            "auth",
            "/login",
            json={"username": "nonexistentuser", "password": "password"},
            timeout=5
        )
        
        assert response.status_code == 401
    
    def test_missing_username_returns_400(self, api_client):
        """Test that missing username returns 400 Bad Request"""
        response = api_client.post(
            "auth",
            "/login",
            json={"password": "password"},
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_missing_password_returns_400(self, api_client):
        """Test that missing password returns 400 Bad Request"""
        response = api_client.post(
            "auth",
            "/login",
            json={"username": "testuser"},
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_empty_username_returns_400(self, api_client):
        """Test that empty username returns 400"""
        response = api_client.post(
            "auth",
            "/login",
            json={"username": "", "password": "password"},
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_empty_password_returns_400(self, api_client):
        """Test that empty password returns 400"""
        response = api_client.post(
            "auth",
            "/login",
            json={"username": "testuser", "password": ""},
            timeout=5
        )
        
        assert response.status_code == 400
    
    @pytest.mark.parametrize("username,password,expected_status", [
        ("testuser", "testpass123", 200),
        ("testuser", "wrongpass", 401),
        ("", "testpass123", 400),
        ("testuser", "", 400),
        ("user@123", "password", 401),
    ])
    def test_login_parametrized(self, api_client, username, password, expected_status):
        """Parametrized test for various login scenarios"""
        response = api_client.post(
            "auth",
            "/login",
            json={"username": username, "password": password},
            timeout=5
        )
        
        assert response.status_code == expected_status


class TestAuthServiceRegistrationBlackBox:
    """Black box tests for user registration"""
    
    def test_register_new_user_success(self, api_client, test_user_data):
        """Test successful user registration"""
        user_data = test_user_data["valid"]
        response = api_client.post(
            "auth",
            "/register",
            json=user_data,
            timeout=5
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "user_id" in data or "message" in data
    
    def test_register_duplicate_user_returns_409(self, api_client):
        """Test that duplicate user registration returns 409 Conflict"""
        user_data = {
            "username": "existinguser",
            "email": "existing@example.com",
            "password": "SecurePass123!"
        }
        
        # First registration
        api_client.post("auth", "/register", json=user_data, timeout=5)
        
        # Duplicate registration
        response = api_client.post(
            "auth",
            "/register",
            json=user_data,
            timeout=5
        )
        
        assert response.status_code == 409
    
    def test_register_invalid_email_returns_400(self, api_client):
        """Test that invalid email format returns 400"""
        user_data = {
            "username": "newuser",
            "email": "notanemail",
            "password": "SecurePass123!"
        }
        response = api_client.post(
            "auth",
            "/register",
            json=user_data,
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_register_missing_fields_returns_400(self, api_client):
        """Test that missing required fields returns 400"""
        user_data = {"username": "newuser"}
        response = api_client.post(
            "auth",
            "/register",
            json=user_data,
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_register_weak_password_returns_400(self, api_client):
        """Test that weak password returns 400"""
        user_data = {
            "username": "newuser",
            "email": "user@example.com",
            "password": "weak"
        }
        response = api_client.post(
            "auth",
            "/register",
            json=user_data,
            timeout=5
        )
        
        assert response.status_code == 400


class TestAuthServiceTokenValidationBlackBox:
    """Black box tests for token validation"""
    
    def test_valid_token_returns_200(self, api_client, api_base_urls):
        """Test that valid token is accepted"""
        # Get token first
        login_response = api_client.post(
            "auth",
            "/login",
            json={"username": "testuser", "password": "testpass123"},
            timeout=5
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Validate token
            response = api_client.get(
                "auth",
                "/validate",
                headers=headers,
                timeout=5
            )
            
            assert response.status_code == 200
    
    def test_invalid_token_returns_401(self, api_client):
        """Test that invalid token returns 401"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = api_client.get(
            "auth",
            "/validate",
            headers=headers,
            timeout=5
        )
        
        assert response.status_code == 401
    
    def test_missing_token_returns_401(self, api_client):
        """Test that missing token returns 401"""
        response = api_client.get(
            "auth",
            "/validate",
            timeout=5
        )
        
        assert response.status_code == 401


class TestAuthServiceLogoutBlackBox:
    """Black box tests for logout functionality"""
    
    def test_logout_invalidates_token(self, api_client):
        """Test that logout invalidates the token"""
        # Login
        login_response = api_client.post(
            "auth",
            "/login",
            json={"username": "testuser", "password": "testpass123"},
            timeout=5
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Logout
            logout_response = api_client.post(
                "auth",
                "/logout",
                headers=headers,
                timeout=5
            )
            
            assert logout_response.status_code in [200, 204]


class TestAuthServiceErrorHandling:
    """Black box tests for error handling"""
    
    def test_malformed_json_returns_400(self, api_base_urls):
        """Test that malformed JSON returns 400"""
        response = requests.post(
            f"{api_base_urls['auth']}/login",
            data="invalid json {",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        assert response.status_code == 400
    
    def test_unsupported_method_returns_405(self, api_base_urls):
        """Test that unsupported HTTP method returns 405"""
        response = requests.delete(
            f"{api_base_urls['auth']}/login",
            timeout=5
        )
        
        assert response.status_code == 405
    
    def test_nonexistent_endpoint_returns_404(self, api_base_urls):
        """Test that non-existent endpoint returns 404"""
        response = requests.get(
            f"{api_base_urls['auth']}/nonexistent",
            timeout=5
        )
        
        assert response.status_code == 404
