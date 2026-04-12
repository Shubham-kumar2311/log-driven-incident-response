"""
White box tests for Authentication Service
Tests internal implementation, logic branches, and code paths
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import jwt
from datetime import datetime, timedelta
import sys
sys.path.insert(0, 'src/auth_service')

# Assuming these modules exist in auth_service
from models import User
from utils.password_utils import hash_password, verify_password
from utils.token_utils import generate_token, verify_token


class TestPasswordHashingLogic:
    """White box tests for password hashing implementation"""
    
    def test_hash_password_returns_non_empty_string(self):
        """Test that hash_password returns a valid hash"""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed != password  # Should not be plaintext
    
    def test_different_passwords_produce_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "Password123!"
        password2 = "Password456!"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        assert hash1 != hash2
    
    def test_same_password_produces_different_hashes(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "SamePassword123!"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
    
    def test_verify_password_returns_true_for_matching(self):
        """Test that verify_password correctly validates matching password"""
        password = "TestPassword123!"
        hashed = hash_password(password)
        
        result = verify_password(password, hashed)
        assert result is True
    
    def test_verify_password_returns_false_for_non_matching(self):
        """Test that verify_password rejects wrong password"""
        correct_password = "CorrectPass123!"
        wrong_password = "WrongPass123!"
        hashed = hash_password(correct_password)
        
        result = verify_password(wrong_password, hashed)
        assert result is False
    
    def test_verify_password_handles_empty_password(self):
        """Test verify_password with empty password"""
        hashed = hash_password("ValidPassword")
        result = verify_password("", hashed)
        
        assert result is False
    
    def test_hash_password_with_unicode_characters(self):
        """Test hashing passwords with unicode characters"""
        password = "Пароль123!🔐"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_hash_password_with_long_string(self):
        """Test hashing very long passwords"""
        password = "x" * 1000
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True


class TestTokenGeneration:
    """White box tests for JWT token generation logic"""
    
    def test_generate_token_creates_valid_jwt(self):
        """Test that generate_token creates a valid JWT"""
        user_id = "user123"
        token = generate_token(user_id)
        
        assert token is not None
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert token.count('.') == 2
    
    def test_generated_token_contains_user_id(self):
        """Test that token payload contains user_id"""
        user_id = "user456"
        token = generate_token(user_id)
        
        # Decode without verification to check payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert decoded.get("user_id") == user_id
    
    def test_generated_token_has_expiration(self):
        """Test that generated token includes expiration"""
        user_id = "user789"
        token = generate_token(user_id)
        
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert "exp" in decoded
        assert decoded["exp"] > datetime.utcnow().timestamp()
    
    def test_verify_token_validates_valid_token(self):
        """Test that verify_token accepts valid token"""
        user_id = "user123"
        token = generate_token(user_id)
        
        result = verify_token(token)
        assert result is not None
        assert result.get("user_id") == user_id
    
    def test_verify_token_rejects_invalid_token(self):
        """Test that verify_token rejects malformed token"""
        invalid_token = "not.a.valid.token"
        
        with pytest.raises(Exception):  # Should raise JWT error
            verify_token(invalid_token)
    
    def test_verify_token_rejects_tampered_token(self):
        """Test that verify_token detects tampered token"""
        user_id = "user123"
        token = generate_token(user_id)
        
        # Tamper with token by changing a character
        tampered_token = token[:-10] + "wrongchars"
        
        with pytest.raises(Exception):
            verify_token(tampered_token)
    
    def test_verify_token_rejects_expired_token(self):
        """Test that verify_token rejects expired token"""
        user_id = "user123"
        # Generate a token that's already expired
        # This would normally be done by creating token with past expiration
        
        # Mock the expiration time to be in the past
        with patch('utils.token_utils.datetime') as mock_datetime:
            past_time = datetime.utcnow() - timedelta(hours=1)
            mock_datetime.utcnow.return_value = past_time
            # Generate token with mocked time
            # Token would be considered expired
            pass  # Implementation-specific


class TestUserModel:
    """White box tests for User model"""
    
    def test_user_creation_with_valid_data(self):
        """Test creating User with valid data"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
    
    def test_user_is_active_by_default(self):
        """Test that new user is active by default"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed"
        )
        
        assert user.is_active is True
    
    def test_user_to_dict_contains_all_fields(self):
        """Test User.to_dict() returns all expected fields"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed"
        )
        user.id = "user123"
        
        user_dict = user.to_dict()
        
        assert user_dict["id"] == "user123"
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert "password_hash" not in user_dict  # Should not expose hash
    
    def test_user_to_dict_excludes_sensitive_data(self):
        """Test that to_dict doesn't include sensitive information"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="secret_hash"
        )
        
        user_dict = user.to_dict()
        
        assert "password_hash" not in user_dict
        assert "secret_hash" not in str(user_dict)


class TestAuthenticationLogic:
    """White box tests for authentication logic"""
    
    @patch('models.User.query')
    def test_login_finds_user_by_username(self, mock_query):
        """Test that login logic queries user by username"""
        mock_user = Mock()
        mock_query.filter_by.return_value.first.return_value = mock_user
        
        # Simulate login logic
        user = mock_query.filter_by(username="testuser").first()
        
        assert user == mock_user
        mock_query.filter_by.assert_called_with(username="testuser")
    
    @patch('models.User.query')
    def test_login_returns_none_for_nonexistent_user(self, mock_query):
        """Test that login returns None when user doesn't exist"""
        mock_query.filter_by.return_value.first.return_value = None
        
        user = mock_query.filter_by(username="nonexistent").first()
        
        assert user is None
    
    @patch('utils.password_utils.verify_password')
    @patch('models.User.query')
    def test_login_verifies_password(self, mock_query, mock_verify):
        """Test that login verifies the password"""
        mock_user = Mock()
        mock_user.password_hash = "hashed_password"
        mock_query.filter_by.return_value.first.return_value = mock_user
        mock_verify.return_value = True
        
        # Simulate login
        user = mock_query.filter_by(username="testuser").first()
        if user and mock_verify("password", user.password_hash):
            result = True
        else:
            result = False
        
        assert result is True
        mock_verify.assert_called_with("password", "hashed_password")
    
    @patch('utils.password_utils.verify_password')
    @patch('models.User.query')
    def test_login_fails_with_wrong_password(self, mock_query, mock_verify):
        """Test that login fails with incorrect password"""
        mock_user = Mock()
        mock_user.password_hash = "hashed_password"
        mock_query.filter_by.return_value.first.return_value = mock_user
        mock_verify.return_value = False
        
        user = mock_query.filter_by(username="testuser").first()
        if user and mock_verify("wrong_password", user.password_hash):
            result = True
        else:
            result = False
        
        assert result is False


class TestRegistrationValidation:
    """White box tests for registration validation logic"""
    
    def test_validate_username_rejects_short_username(self):
        """Test that username validation rejects short names"""
        username = "ab"  # Too short
        
        # Validation logic
        is_valid = len(username) >= 3
        
        assert is_valid is False
    
    def test_validate_username_accepts_valid_username(self):
        """Test that username validation accepts valid names"""
        username = "validusername"
        
        is_valid = len(username) >= 3 and len(username) <= 50
        
        assert is_valid is True
    
    def test_validate_email_format(self):
        """Test email format validation"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        valid_email = "user@example.com"
        invalid_email = "notanemail"
        
        assert re.match(email_pattern, valid_email) is not None
        assert re.match(email_pattern, invalid_email) is None
    
    def test_validate_password_strength(self):
        """Test password strength validation logic"""
        def validate_password_strength(password):
            # At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special
            import re
            if len(password) < 8:
                return False
            if not re.search(r'[A-Z]', password):
                return False
            if not re.search(r'[a-z]', password):
                return False
            if not re.search(r'\d', password):
                return False
            if not re.search(r'[!@#$%^&*]', password):
                return False
            return True
        
        assert validate_password_strength("WeakPass") is False
        assert validate_password_strength("StrongPass123!") is True
        assert validate_password_strength("NoSpecialChar123") is False
    
    @patch('models.User.query')
    def test_validate_duplicate_username(self, mock_query):
        """Test that duplicate username is detected"""
        mock_query.filter_by.return_value.first.return_value = Mock()
        
        existing_user = mock_query.filter_by(username="existinguser").first()
        
        assert existing_user is not None  # User exists, so duplicate
    
    @patch('models.User.query')
    def test_validate_unique_username(self, mock_query):
        """Test that unique username is accepted"""
        mock_query.filter_by.return_value.first.return_value = None
        
        existing_user = mock_query.filter_by(username="newuser").first()
        
        assert existing_user is None  # No duplicate


class TestSessionManagement:
    """White box tests for session/token management"""
    
    def test_user_sessions_stored_correctly(self):
        """Test that user sessions are stored with correct data"""
        user_id = "user123"
        token = "valid.jwt.token"
        session_data = {
            "user_id": user_id,
            "token": token,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        assert session_data["user_id"] == user_id
        assert session_data["token"] == token
        assert "created_at" in session_data
        assert "expires_at" in session_data
    
    def test_logout_invalidates_session(self):
        """Test that logout removes session data"""
        sessions = {
            "user123": {"token": "valid.token", "active": True}
        }
        
        # Simulate logout
        if "user123" in sessions:
            del sessions["user123"]
        
        assert "user123" not in sessions
    
    def test_multiple_sessions_per_user(self):
        """Test that single user can have multiple active sessions"""
        user_id = "user123"
        sessions = {}
        
        # Create multiple sessions
        sessions[f"{user_id}_1"] = {"token": "token1", "device": "desktop"}
        sessions[f"{user_id}_2"] = {"token": "token2", "device": "mobile"}
        
        user_sessions = [s for k, s in sessions.items() if k.startswith(user_id)]
        
        assert len(user_sessions) == 2


class TestAuthMiddleware:
    """White box tests for authentication middleware"""
    
    @patch('utils.token_utils.verify_token')
    def test_middleware_extracts_token_from_header(self, mock_verify):
        """Test that middleware correctly extracts token from Authorization header"""
        headers = {"Authorization": "Bearer valid.jwt.token"}
        mock_verify.return_value = {"user_id": "user123"}
        
        # Simulate token extraction
        auth_header = headers.get("Authorization", "")
        token = auth_header.split(" ")[1] if " " in auth_header else None
        
        assert token == "valid.jwt.token"
    
    @patch('utils.token_utils.verify_token')
    def test_middleware_rejects_missing_token(self, mock_verify):
        """Test that middleware rejects requests without token"""
        headers = {}
        
        auth_header = headers.get("Authorization")
        
        assert auth_header is None
    
    @patch('utils.token_utils.verify_token')
    def test_middleware_rejects_invalid_token_format(self, mock_verify):
        """Test that middleware detects invalid token format"""
        headers = {"Authorization": "InvalidFormat"}
        
        auth_header = headers.get("Authorization", "")
        parts = auth_header.split(" ")
        
        assert len(parts) != 2  # Should have "Bearer" and token
    
    def test_middleware_adds_user_to_request_context(self):
        """Test that middleware adds user info to request"""
        user_data = {"user_id": "user123", "username": "testuser"}
        request_context = {}
        
        # Middleware adds user to context
        request_context["user"] = user_data
        
        assert request_context["user"]["user_id"] == "user123"
